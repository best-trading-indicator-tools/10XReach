import os, random, subprocess, re, tempfile
import sys

# Add project root to Python path to allow importing video_processor
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from video_processor import get_ffmpeg_path

vid_dir = 'videos'
files = [f for f in os.listdir(vid_dir) if f.lower().endswith('.mp4')]
if not files:
    raise SystemExit('No mp4 files in videos/')
filename = random.choice(files)
print('Chosen file:', filename)
orig_path = os.path.join(vid_dir, filename)
ffmpeg = get_ffmpeg_path()

# temp outputs
out1 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
out2 = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name

base_filters = (
    "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
    "zoompan=z='min(max(1,zoom)+0.000115,1.1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:d=1:fps=30," \
    "drawbox=x=2:y=2:w=2:h=2:color=white@0.9:t=fill,setsar=1,eq=brightness=0.005:contrast=1.005"
)

subprocess.run([ffmpeg,'-i',orig_path,'-vf',base_filters,'-t','29','-c:v','libx264','-b:v','6000k','-an','-y',out1],stdout=subprocess.PIPE,stderr=subprocess.PIPE)

ssim_cmd = [ffmpeg,'-i',orig_path,'-i',out1,'-filter_complex',
            '[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[v0];'
            '[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[v1];'
            '[v0][v1]ssim','-f','null','-']
res1 = subprocess.run(ssim_cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
match1 = re.search(r'SSIM.*?All:\s*([0-9\.]+)', res1.stderr)
val1 = float(match1.group(1))*100 if match1 else None
print(f'SSIM without rotation: {val1:.2f}%')

rot_filters = base_filters.replace('eq=brightness=0.005:contrast=1.005','rotate=0.01745:bilinear=0,eq=brightness=0.005:contrast=1.005')
subprocess.run([ffmpeg,'-i',orig_path,'-vf',rot_filters,'-t','29','-c:v','libx264','-b:v','6000k','-an','-y',out2],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
ssim_cmd2 = [ffmpeg,'-i',orig_path,'-i',out2,'-filter_complex',
            '[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[v0];'
            '[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[v1];'
            '[v0][v1]ssim','-f','null','-']
res2 = subprocess.run(ssim_cmd2,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
match2 = re.search(r'SSIM.*?All:\s*([0-9\.]+)', res2.stderr)
val2 = float(match2.group(1))*100 if match2 else None
print(f'SSIM with rotation: {val2:.2f}%')

os.unlink(out1)
os.unlink(out2) 