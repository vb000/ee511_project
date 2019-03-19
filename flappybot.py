import random
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras import optimizers
from keras.models import load_model

MAX_EPSILON_ITERS = 100000
MIN_EPSILON = 0.1
MEM_SIZE = 100
BATCH_SIZE = 32

class flappybot:
    def __init__(self, load, train):
        # parameters
        self.epsilon = 1.0
        self.gamma = 0.95
        self.iter_count = 0
        self.episode = 1
        self.lr = 0.001
        self.scores = []

        # Initialize memory
        self.memory = deque(maxlen=MEM_SIZE)
        for i in range(MEM_SIZE):
            rand_state = np.random.rand(1, 4)
            rand_action = 1 if random.random() > 0.5 else 0
            rand_reward = random.choice([1, -1000])
            rand_state_n = np.random.rand(1, 4)
            self.memory.append((rand_state, rand_action, rand_reward, rand_state_n))

        # model
        if load:
            self.model = load_model('flappybot.h5')
        else:
            self.model = Sequential()
            self.model.add(Dense(units=32, activation='relu', input_dim=4))
            self.model.add(Dropout(0.1))
            self.model.add(Dense(units=32, activation='relu'))
            self.model.add(Dropout(0.1))
            self.model.add(Dense(units=2, activation='softmax'))

            # optimizer
            optimizer = optimizers.Adam(lr=self.lr)
            self.model.compile(optimizer=optimizer, loss='mse')
        self.train = train
        
        self.prev_state = np.random.rand(1, 4)
        self.prev_action = 1

    def remember(self, state, action, reward, state_n):
        self.memory.append((state, action, reward, state_n))

    def replay(self):
        batch = random.sample(self.memory, BATCH_SIZE)
        for (state, action, reward, state_n) in batch:
            target = reward
            if reward == 1:
                target = reward + self.gamma * np.amax(self.model.predict(state_n)[0])

            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

    def act(self, delX, delY1, delY2, vel, status, score):
        # Current state
        delX_norm = delX/500
        delY1_norm = delY1/500
        delY2_norm = delY2/500
        vel_norm = vel/20
        curr_state = np.array([[delX_norm, delY1_norm, delY2_norm, vel_norm]])
        
        # Reward for previous action
        #reward = 1 if status else -1000
        if status:
            if delX_norm < 0.1 and delY1_norm > 0.15 and delY1_norm < 0.35:
                reward = 500
            else:
                reward = 1
        else:
            self.episode += 1
            self.scores.append(score)
            reward = -1000


        # Epsilon-greedy strategy for first few iterations
        if self.train and random.random() < self.epsilon:
            action = 0 if random.random() < 0.7 else 1
            self.iter_count += 1
        else:
            q_vals = self.model.predict(curr_state)[0]
            action = 0 if q_vals[0] > q_vals[1] else 1
            print("Qs =", q_vals[0], q_vals[1], "iter_count =", self.iter_count, "epsilon =", self.epsilon,\
            "state =", curr_state, "episode =", self.episode, "score =", score, "reward =", reward)

        if self.iter_count < MAX_EPSILON_ITERS:
            self.iter_count += 1
            if self.epsilon > MIN_EPSILON:
                self.epsilon *= (1 - (self.iter_count/MAX_EPSILON_ITERS))

        if self.train:
            self.remember(self.prev_state, self.prev_action, reward, curr_state)
            self.replay()
            self.prev_state = curr_state
            self.prev_action = action

        return (action == 1)
        
    def save(self):
        self.model.save('flappybot.h5')
        
        with open('score.txt', 'w') as f:
            for score in self.scores:
                f.write("%s\n" % score)
        f.close()
