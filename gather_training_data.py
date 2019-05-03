"""Gather training data from the game"""

from __future__ import print_function

import argparse
import json
import time

import numpy as np
import pygame
import tensorflow as tf

import gym

import gym_2048
import training_data

grid_size = 70

class Exiting(Exception):
    def __init__(self):
        super(Exiting, self).__init__()

def gather_training_data(env, model, seed=None):
    """Gather training data from letting the user play the game"""
    # Data is a list of input and outputs
    data = training_data.training_data()
    # Initialise seed for environment
    if seed:
        env.seed(seed)
    else:
        env.seed()
    observation = env.reset()
    print("User cursor keys to play, q to quit")
    try:
        while True:
            # Loop around performing moves
            action = None
            env.render()

            # Display with pygame
            black = (0, 0, 0)
            grey = (128, 128, 128)
            blue = (0, 0, 128)
            white = (255, 255, 255)
            tile_colour_map = {
                2: (255, 0, 0),
                4: (224, 32, 0),
                8: (192, 64, 0),
                16: (160, 96, 0),
                32: (128, 128, 0),
                64: (96, 160, 0),
                128: (64, 192, 0),
                256: (32, 224, 0),
                512: (0, 255, 0),
                1024: (0, 224, 32),
                2048: (0, 192, 64),
            }
            # Background
            screen.fill(black)
            # Board
            pygame.draw.rect(screen, grey, (0, 0, grid_size * 4, grid_size * 4))
            myfont = pygame.font.SysFont('Tahome', 30)
            for i, o, in enumerate(observation):
                 x = i % 4
                 y = i // 4
                 if o:
                     pygame.draw.rect(screen, tile_colour_map[o], (x * grid_size, y * grid_size, grid_size, grid_size))
                     text = myfont.render(str(o), False, white)
                     text_rect = text.get_rect()
                     width = text_rect.width
                     height = text_rect.height
                     assert width < grid_size
                     assert height < grid_size
                     screen.blit(text, (x * grid_size + grid_size / 2 - text_rect.width / 2,
                         y * grid_size + grid_size / 2 - text_rect.height / 2))

            pygame.display.update()

            ## Get predictions from model
            if model:
                normalised_observation = (observation - 64.) / 188.
                predictions = model.predict(np.reshape(normalised_observation, (-1, 16))).reshape((4))
                predicted_action = np.argmax(predictions)
                #print(predictions)

                # Report predicted rewards for actions
                dir_dict = { 0: 'up', 1: 'right', 2: 'down', 3: 'left'}
                dir_reward = [(dir_dict[i], p) for i, p in enumerate(list(predictions))]
                dir_reward.sort(key=lambda x: x[1], reverse=True)
                for direction, reward in dir_reward:
                    print('{}: {:.3f}'.format(direction, reward))

            # Ask user for action
            while True:
                # Loop waiting for valid input
                event = pygame.event.wait()
                if event.type == pygame.KEYDOWN:
                    key_action_map = {
                        pygame.K_UP: 0,
                        pygame.K_RIGHT: 1,
                        pygame.K_DOWN: 2,
                        pygame.K_LEFT: 3
                    }
                    if event.key in key_action_map:
                        action = key_action_map[event.key]
                        break
                    if event.key == pygame.K_q:
                        raise Exiting
                    if model and (event.key == pygame.K_a):
                        # Auto-select best action according to model
                        action = predicted_action
                        break
                if event.type == pygame.QUIT:
                    raise Exiting
            # Read and discard the keyup event
            print("Read action {}".format(action))

            # Add this data to the data collection
            new_observation, reward, done, info = env.step(action)
            if np.array_equal(observation, new_observation):
                print("Suppressing recording of illegal move")
            else:
                data.add(observation, action, reward, new_observation, done)
            observation = new_observation
            print()

            if done:
                # Draw final board
                env.render()
                print("End of game")
                break
    except Exiting:
        print("Exiting...")

    return data

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', default=None, help="Input trained model to get predictions from (optional)")
    parser.add_argument('--output', '-o', default='data_{}.csv'.format(int(time.time())), help="Set the output file name")
    parser.add_argument('--seed', type=int, default=None, help="Set the seed for the game")
    parser.add_argument('-p', '--params', default='params.json', help='File defining hyperparameters to try')
    args = parser.parse_args()
    # Initialise environment
    env = gym.make('2048-v0')

    # Initialise pygame for detecting keypresses
    pygame.init()
    screen = pygame.display.set_mode((grid_size * 4, grid_size * 4), 0, 32)
    pygame.font.init()

    # Load hyperparameters from JSON file
    with open(args.params, 'r') as f:
        params = json.load(f)

    # Load model
    if args.input:
        model = tf.keras.models.load_model(args.input)
    else:
        model = None

    data = gather_training_data(env, model, seed=args.seed)

    # Close the environment
    env.close()

    print("Got {} data values".format(data.size()))

    data.export_csv(args.output)
