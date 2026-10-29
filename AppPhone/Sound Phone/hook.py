from pathlib import Path

def after_apk_build(toolchain):
    """Hook để sửa AndroidManifest.xml"""
    manifest_file = Path(toolchain._dist.dist_dir) / "src" / "main" / "AndroidManifest.xml"
    text = manifest_file.read_text(encoding="utf-8")
    
    # Tìm service tag của bạn
    service_name = ".ServiceAlarmService"  # Tên service trong manifest
    pos = text.find(f'android:name="{service_name}"')
    
    if pos != -1:
        # Chèn foregroundServiceType (mediaPlayback cho phát nhạc)
        end = text.find("/>", pos)
        text = (text[:end] + 
                ' android:foregroundServiceType="mediaPlayback"' + 
                text[end:])
        manifest_file.write_text(text, encoding="utf-8")
        print("✅ Đã thêm foregroundServiceType vào manifest")