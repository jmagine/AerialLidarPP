'''*-----------------------------------------------------------------------*---
                                                          Authors: Jason Ma
                                                          Date   : Feb 11, 2018
    File Name  : tif_gen.py
    Description: Generates a DEM using whatever scheme desired.
---*-----------------------------------------------------------------------*'''

import matplotlib.pyplot as plt
import numpy as np

'''[Config vars]------------------------------------------------------------'''
FILENAME = "chessboard.tif"
I_WIDTH = 200
I_HEIGHT = 200

'''[create_image]--------------------------------------------------------------
  Creates image according to algorithm, where each value in returned array
  corresponds to a pixel representing height in the final tif image.
----------------------------------------------------------------------------'''
def create_image():
  image = np.zeros((I_HEIGHT, I_WIDTH))

  ''' 
  # Dense Diamond pattern
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if (abs(x - I_WIDTH / 2) + abs(y - I_HEIGHT / 2)) % 5 == 0 or (abs(x - I_WIDTH / 2) + abs(y - I_HEIGHT / 2)) % 5 == 1:
        image[y][x] = 5
  '''


  # Random squares
  from random import randint

  for i in range(1000):
    s_x = randint(0, I_WIDTH - 11)
    s_y = randint(0, I_HEIGHT - 11)
    s_w = randint(3, 10)
    s_h = randint(3, 10)
    s_z = randint(3, 15)

    for x in range(s_x, s_x + s_w):
      for y in range(s_y, s_y + s_h):
        image[y][x] = s_z + randint(-2, 2)
  

  '''
  # Chessboard
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if (x % 20 < 10 and y % 20 < 10) or (x % 20 >= 10 and y % 20 >= 10):
        image[y][x] = 5
  '''

  '''
  # Big square in middle
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if abs(x - I_WIDTH / 2) < 50 and abs(y - I_HEIGHT / 2) < 50:
        image[y][x] = 5
  '''

  '''
  # Hollow square in middle
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if abs(x - I_WIDTH / 2) < 50 and abs(y - I_HEIGHT / 2) < 50:
        image[y][x] = 5

  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if abs(x - I_WIDTH / 2) < 40 and abs(y - I_HEIGHT / 2) < 40:
        image[y][x] = 0
  '''

  return image

'''[main]----------------------------------------------------------------------
  Drives program, creates image and saves it using matplotlib, which uses PIL
  underneath (simple this way).
----------------------------------------------------------------------------'''
def main():
  image = create_image()
  plt.imsave(FILENAME, image)

if __name__ == '__main__':
  main()