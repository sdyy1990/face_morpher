"""
::

  Morph from source to destination face or
  Morph through all images in a folder

  Usage:
    morpher.py (--src=<src_path> --dest=<dest_path> | --images=<folder>)
              [--width=<width>] [--height=<height>]
              [--num=<num_frames>] [--fps=<frames_per_second>]
              [--out_frames=<folder>] [--out_video=<filename>]
              [--alpha] [--plot] [--dots] [--tri]

  Options:
    -h, --help              Show this screen.
    --src=<src_imgpath>     Filepath to source image (.jpg, .jpeg, .png)
    --dest=<dest_path>      Filepath to destination image (.jpg, .jpeg, .png)
    --images=<folder>       Folderpath to images
    --width=<width>         Custom width of the images/video [default: 500]
    --height=<height>       Custom height of the images/video [default: 600]
    --num=<num_frames>      Number of morph frames [default: 20]
    --fps=<fps>             Number frames per second for the video [default: 10]
    --out_frames=<folder>   Folder path to save all image frames
    --out_video=<filename>  Filename to save a video
    --alpha                 Flag to save transparent background [default: False]
    --plot                  Flag to plot images [default: False]
    --dots                  Flag to plot the XXX dots.
    --tri                   Flag to plot the delauney triangulation.
    --version               Show version.
"""
from docopt import docopt
import scipy.ndimage
import numpy as np
import os

from facemorpher import locator
from facemorpher import aligner
from facemorpher import warper
from facemorpher import blender
from facemorpher import plotter
from facemorpher import videoer

from skimage.draw import circle
from skimage.draw import line
from skimage.draw import line_aa
import scipy.spatial as spatial

def verify_args(args):
  if args['--images'] is None:
    valid = os.path.isfile(args['--src']) & os.path.isfile(args['--dest'])
    if not valid:
      print('--src=%s or --dest=%s file does not exist. Double check the supplied paths' % (
        args['--src'], args['--dest']))
      exit(1)
  else:
    valid = os.path.isdir(args['--images'])
    if not valid:
      print('--images=%s is not a valid directory' % args['--images'])
      exit(1)

def load_image_points(path, size):
  img = scipy.ndimage.imread(path)[..., :3]
  points = locator.face_points(path)

  if len(points) == 0:
    print('No face in %s' % path)
    return None, None
  else:
    return aligner.resize_align(img, points, size)

def load_valid_image_points(imgpaths, size):
  for path in imgpaths:
    img, points = load_image_points(path, size)
    if img is not None:
      print(path)
      yield (img, points)

def list_imgpaths(images_folder=None, src_image=None, dest_image=None):
  if images_folder is None:
    yield src_image
    yield dest_image
  else:
    for fname in os.listdir(images_folder):
      if (fname.lower().endswith('.jpg') or
         fname.lower().endswith('.png') or
         fname.lower().endswith('.jpeg')):
        yield os.path.join(images_folder, fname)

def alpha_image(img, points):
  mask = blender.mask_from_points(img.shape[:2], points)
  return np.dstack((img, mask))

def adddots(img, points):
    r = 6
    for i in xrange(len(points)):
        rr, cc = circle(points[i,1],points[i,0], r)
        img[rr, cc] = [105,105,0]

def addtriangle(img, points):
    delau  = spatial.Delaunay(points)
    pl = points[delau.simplices]
    for x in pl:
        rr, cc, val = line_aa (x[0,1],x[0,0],x[1,1],x[1,0])
        img[rr,cc] = [200,105,0]
        rr, cc, val = line_aa (x[2,1],x[2,0],x[1,1],x[1,0])
        img[rr,cc] = [200,105,0]
        rr, cc,val = line_aa (x[0,1],x[0,0],x[2,1],x[2,0])
        img[rr,cc] = [200,105,0]



def morph(src_img, src_points, dest_img, dest_points,
          video, width=250, height=300, num_frames=20, fps=10,
          out_frames=None, out_video=None, alpha=False, plot=False, dots=False, triangle=False):
  """
  Create a morph sequence from source to destination image

  :param src_img: ndarray source image
  :param src_img: source image array of x,y face points
  :param dest_img: ndarray destination image
  :param dest_img: destination image array of x,y face points
  :param video: facemorpher.videoer.Video object
  """
  size = (height, width)
  stall_frames = np.clip(int(fps*0.15), 1, fps)  # Show first & last longer
  plt = plotter.Plotter(plot, num_images=num_frames, folder=out_frames)
  num_frames -= (stall_frames * 2)  # No need to process src and dest image

  if dots:
      adddots(src_img, src_points)
  if triangle:
      addtriangle(src_img,src_points)
  plt.plot_one(src_img,'save')

  video.write(src_img, stall_frames)

  # Produce morph frames!
  for percent in np.linspace(1, 0, num=num_frames):
    points = locator.weighted_average_points(src_points, dest_points, percent)
    src_face = warper.warp_image(src_img, src_points, points, size )
    end_face = warper.warp_image(dest_img, dest_points, points, size)
    average_face = blender.weighted_average(src_face, end_face, percent)
    average_face = alpha_image(average_face, points) if alpha else average_face
    if dots:
        adddots(average_face, points);
    if triangle:
      addtriangle(average_face,points)
    plt.plot_one(average_face, 'save')
    video.write(average_face)

  if dots:
      adddots(dest_img, dest_points)
  if triangle:
      addtriangle(dest_img,dest_points)

  plt.plot_one(dest_img,'save')
  video.write(dest_img, stall_frames)

  plt.show()

def morpher(imgpaths, width=250, height=300, num_frames=20, fps=10,
            out_frames=None, out_video=None, alpha=False, plot=False, dots=False, triangle=False):
  """
  Create a morph sequence from multiple images in imgpaths

  :param imgpaths: array or generator of image paths
  """
  video = videoer.Video(out_video, fps, width, height)
  images_points_gen = load_valid_image_points(imgpaths, (height, width))
  src_img, src_points = next(images_points_gen)
  for dest_img, dest_points in images_points_gen:
    morph(src_img, src_points, dest_img, dest_points, video,
          width, height, num_frames, fps, out_frames, out_video, alpha, plot, dots, triangle)
    src_img, src_points = dest_img, dest_points
  video.end()

def main():
  args = docopt(__doc__, version='Face Morpher 1.0')
  verify_args(args)

  morpher(list_imgpaths(args['--images'], args['--src'], args['--dest']),
          int(args['--width']), int(args['--height']),
          int(args['--num']), int(args['--fps']),
          args['--out_frames'], args['--out_video'],
          args['--alpha'], args['--plot'], args['--dots'], args['--tri'])

if __name__ == "__main__":
  main()
