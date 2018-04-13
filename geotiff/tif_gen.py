'''*-----------------------------------------------------------------------*---
                                                          Authors: Jason Ma
                                                          Date   : Feb 11, 2018
    File Name  : tif_gen.py
    Description: Generates a DEM using whatever scheme desired.
---*-----------------------------------------------------------------------*'''

import matplotlib.pyplot as plt
import numpy as np

'''[Config vars]------------------------------------------------------------'''
FILENAME = "../images/sine-1f-20a.tif"
I_WIDTH = 200
I_HEIGHT = 200

OBSTACLE_HEIGHT = 5

NOISY_TERRAIN = True

freq = 1
amp = 20
offset_z = 3

'''[create_image]--------------------------------------------------------------
  Creates image according to algorithm, where each value in returned array
  corresponds to a pixel representing height in the final tif image.
----------------------------------------------------------------------------'''
def create_image():

  # Generate a more noisy starting image, with some elevation changes throughout
  if NOISY_TERRAIN:
    from random import randint
    from math import sqrt

    # Use numpy's random init for noise
    image = np.random.randint(low=0, high=2, size=(I_HEIGHT, I_WIDTH))

    # Total height change
    #for i in range(10):
    for j in range(100):
      s_x = randint(-25, I_WIDTH - 25)
      s_y = randint(-25, I_HEIGHT - 25)
      s_r = randint(50, 100)
      s_z = randint(-1, 1)

      for x in range(s_x - s_r, s_x + s_r):
        for y in range(s_y - s_r, s_y + s_r):
          if x >= 0 and x < I_WIDTH and y >= 0 and y < I_HEIGHT:
            if sqrt(abs(x - s_x)**2 + abs(y - s_y)**2) < s_r:
              image[y][x] += s_z


  # Generate flat starting image
  else:
    image = np.zeros((I_HEIGHT, I_WIDTH))

  
  # Sine wave pattern
  from math import sqrt, sin
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      image[y][x] += amp * sin(freq * sqrt((x - I_WIDTH / 2)**2 + (y - I_HEIGHT / 2)**2) - 1.570796) + offset_z
  

  ''' 
  # Dense Diamond pattern
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if (abs(x - I_WIDTH / 2) + abs(y - I_HEIGHT / 2)) % 5 == 0 or (abs(x - I_WIDTH / 2) + abs(y - I_HEIGHT / 2)) % 5 == 1:
        image[y][x] += OBSTACLE_HEIGHT
  '''

  '''
  # Random trees
  from random import randint
  from math import sqrt

  for i in range(1000):
    s_x = randint(-9, I_WIDTH - 1)
    s_y = randint(-9, I_HEIGHT - 1)
    s_r = randint(3, 10)
    s_z = randint(3, 15)

    if x >= 0 and x < I_WIDTH and y >= 0 and y < I_HEIGHT:
      s_b = image[y][x]
    else:
      s_b = 0

    for x in range(s_x - s_r, s_x + s_r):
      for y in range(s_y - s_r, s_y + s_r):
        if x >= 0 and x < I_WIDTH and y >= 0 and y < I_HEIGHT:
          if sqrt((x - s_x)**2 + (y - s_y)**2) <= s_r:
            image[y][x] = s_b + s_z + randint(-1, 1) * 0.5
  '''

  '''
  # Chessboard
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if (x % 20 < 10 and y % 20 < 10) or (x % 20 >= 10 and y % 20 >= 10):
        image[y][x] += OBSTACLE_HEIGHT
  '''

  '''
  # Big square in middle
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if abs(x - I_WIDTH / 2) < 50 and abs(y - I_HEIGHT / 2) < 50:
        image[y][x] += OBSTACLE_HEIGHT
  '''

  '''
  # Hollow square in middle
  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if abs(x - I_WIDTH / 2) < 50 and abs(y - I_HEIGHT / 2) < 50:
        image[y][x] += OBSTACLE_HEIGHT

  for x in range(image.shape[0]):
    for y in range(image.shape[1]):
      if abs(x - I_WIDTH / 2) < 40 and abs(y - I_HEIGHT / 2) < 40:
        image[y][x] -= OBSTACLE_HEIGHT
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
