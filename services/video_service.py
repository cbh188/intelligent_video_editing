import os
from utils import video_util
import cv2
import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1
from facenet_pytorch import MTCNN


def video_editing(video_id, student_id, video_url, image_url, threshold=0.8):
    """
            人脸匹配的方法。

            参数:
                video_id: 选中要剪辑的视频id
                student_id: 选中的要剪辑出的人脸的学生id
                video_url: 选中要剪辑的视频url
                image_url: 选中的要剪辑出的人脸的url
                threshold: 匹配阈值，小于阈值则人脸匹配

            返回:
                output_url: 剪辑后视频的url

            """
    # 获取初始url
    base_url = "C:/work/WebstormProjects/intelligent_video_editing-web/public"
    image_url = base_url + image_url
    video_url = base_url + video_url
    # 获取设备
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    print('在该设备上运行: {}'.format(device))
    # 导入模型以及训练好的权重
    mtcnn = MTCNN(keep_all=True, device=device)
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

    # 读取学生照片并进行人脸检测对齐获取人脸特征向量操作
    stu_img = cv2.imread(image_url)
    stu_img = cv2.cvtColor(stu_img, cv2.COLOR_BGR2RGB)
    stu_img_aligned, stu_img_boxes = detect_faces(stu_img, mtcnn)
    stu_img_emb = get_embeddings(stu_img_aligned, resnet, device)

    # 读取视频
    cap = cv2.VideoCapture(video_url)

    result_frames = []
    # 读取视频帧，并获取当前帧的索引
    frame_index = 0
    # 读取视频帧
    while True:
        # 增加帧索引
        frame_index += 1

        ret, frame = cap.read()
        if not ret:
            break

        # 打印当前帧索引
        print("\r当前帧:{}".format(frame_index), end='')

        # 对视频每一帧进行人脸检测对齐
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_aligned, frame_boxes = detect_faces(frame_rgb, mtcnn)

        # 如果检测到人脸
        if frame_aligned:
            # 这里得到的frame_emb是图像检测到的所有人脸的向量堆叠起来的结果
            frame_emb = get_embeddings(frame_aligned, resnet, device)
            # 遍历每个检测到的人脸
            for i, box in enumerate(frame_boxes):
                # 计算人脸间的特征距离
                dist = (frame_emb[i] - stu_img_emb[0]).norm().item()

                if dist < threshold:
                    result = '匹配'
                    # frame_with_box = cv2.rectangle(frame_rgb, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 5)
                    # 如果匹配到人脸，则将当前帧添加到结果帧列表中
                    result_frames.append(frame_rgb)
                else:
                    result = '不匹配'

                print('\n第{}帧人脸{}{} dist为{}'.format(frame_index, i, result, dist))

    print('\n结束')

    # 保存剪辑后的视频到指定文件夹中（在实际应用时图片视频都上传到服务器）
    if len(result_frames) > 0:
        output_folder = base_url + '/output'
        if not os.path.isdir(output_folder):
            os.makedirs(output_folder)

        output_url = output_folder + '/video_{}_student_{}.avi'.format(video_id, student_id)
        print(output_url)

        dim = result_frames[0].shape[1], result_frames[0].shape[0]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        video = cv2.VideoWriter(output_url, fourcc, 18.0, dim)
        for frame in result_frames:
            video.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))
        video.release()

        # 关闭视频文件
        cap.release()
        url = video_util.avi_to_web_mp4(output_url)
        return url
    else:
        return "视频中没有匹配的人脸"

# 人脸检测与对齐
def detect_faces(image, mtcnn):
    """
            人脸检测与对齐

            参数:
                image: 选中需要人脸检测的图片
                mtcnn: 导入的mtcnn模型

            返回:
                aligned: 所有检测到的人脸图像堆叠起来的列表
                boxes: 检测到的人脸框列表。每个框由四个坐标值表示，通常是左上角和右下角的(x, y)坐标。这些框用于定位图像中的人脸位置。

            """
    # 进行人脸检测和处理，其中x_aligned, prob是检测到的人脸图像和概率
    x_aligned, prob = mtcnn(image, return_prob=True)
    boxes, _ = mtcnn.detect(image)
    # print(x_aligned)
    try:
        if x_aligned is None:
            raise ValueError("x_aligned is None, cannot perform further operations.")
    except ValueError as e:
        # 捕获到 ValueError 异常，并打印出错消息
        print("An error occurred:", e)
        return [], []

    aligned = []

    if x_aligned is not None:
        # print('检测到的人脸及其概率: {:8f}'.format(prob[0]))
        # image = Image.fromarray(image)
        # 可视化检测结果
        # draw = ImageDraw.Draw(image)
        # for box in boxes:
        #     draw.rectangle(box.tolist(), outline=(255, 0, 0), width=6)
        # plt.figure()
        # plt.imshow(image)
        aligned.append(x_aligned)
        # plt.show()
    else:
        print("未检测到人脸")
    return aligned, boxes

# 获取人脸图像的特征向量
def get_embeddings(img, resnet, device):
    """
            获取人脸图像的特征向量

            参数:
                img: 人脸图像
                resnet: 导入的resnet模型
                device: 设备

            返回:
                embedding: 人脸图像的特征向量

            """
    if not isinstance(img, list):
        img = [img]
    # 将图像列表堆叠在一起，创建一个新的张量，其中每个图像都是张量的一部分。
    aligned = torch.stack(img).to(device)
    # 将 aligned 张量中的第一个维度（批次维度）压缩掉，因为在堆叠时会在批次维度上增加一个维度，而这里我们只想要单个图像的张量。
    aligned = aligned.squeeze(0)
    embedding = resnet(aligned).detach().cpu()
    return embedding