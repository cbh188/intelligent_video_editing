import subprocess


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