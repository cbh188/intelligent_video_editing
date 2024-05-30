import subprocess
from datetime import datetime

from ffmpy import FFmpeg
from moviepy.editor import *
def avi_to_web_mp4(input_file_path):
    '''
    ffmpeg -i test_result.avi -vcodec h264 test_result.mp4
    @param: [in] input_file_path 带avi或mp4的非H264编码的视频的全路径
    @return: [output] output_file_path 生成的H264编码视频的全路径
    '''
    output_file_path = input_file_path[:-3] + 'mp4'
    cmd = 'ffmpeg -y -i {} -vcodec h264 {}'.format(input_file_path, output_file_path)
    subprocess.call(cmd, shell=True)
    return output_file_path

def concat_video(video_list, output_name):
    '''
    @param: [in] video_list 视频列表
    @param: [in] output_name 输出视频的名称
    '''
    L = []
    for x in video_list:
        video = VideoFileClip(x)
        L.append(video)
    final_clip = concatenate_videoclips(L)
    output_dir = "C:/work/WebstormProjects/intelligent_video_editing-web/public/output"
    final_clip.to_videofile(os.path.join(output_dir, output_name), fps=24, remove_temp=True)

def video_add_audio(video_path, audio_path, output_dir, create_by):
    _ext_video = os.path.basename(video_path).strip().split('.')[-1]
    _ext_audio = os.path.basename(audio_path).strip().split('.')[-1]
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    output_name = create_by + current_time
    if _ext_audio not in ['mp3', 'wav']:
        raise Exception('audio format not support')
    _codec = 'copy'
    if _ext_audio == 'wav':
        _codec = 'aac'
    result = output_dir + '/{}.{}'.format(output_name, _ext_video)
    ff = FFmpeg(
        inputs={video_path: None, audio_path: None},
        outputs={result: '-map 0:v -map 1:a -c:v copy -c:a {} -shortest'.format(_codec)})
    print(ff.cmd)
    ff.run()
    return result