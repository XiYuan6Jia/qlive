from PIL import Image

def extract_frames(gif_path,start_frame=0):
    """
    将GIF文件分解为帧列表
    :param gif_path: GIF文件路径
    :return: 包含所有帧的列表
    """
    frames = []
    try:
        with Image.open(gif_path) as img:
            for frame in range(start_frame, img.n_frames):
                img.seek(frame)
                frames.append(img.copy())
    except Exception as e:
        print(f"处理GIF文件时出错: {e}")
    return frames

if __name__ == "__main__":
    # 示例用法
    gif_file = "animations/default.gif"  # 替换为实际的GIF文件路径
    frames = extract_frames(gif_file)
    
    print(f"成功提取 {len(frames)} 帧")
    # 可以选择保存每一帧
    for i, frame in enumerate(frames):
        frame.save(f"frame_{i}.png")
        print(f"已保存第 {i} 帧")
