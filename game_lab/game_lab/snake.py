import random
import time
import os

class SnakeGame:
    def __init__(self, width=10, height=10):
        self.width = width
        self.height = height
        self.snake = [(0, 0)]
        self.direction = 'right'
        self.apple = self.generate_apple()

    def generate_apple(self):
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.snake:
                return (x, y)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display(self):
        self.clear_screen()
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.snake:
                    print('#', end=' ')
                elif (x, y) == self.apple:
                    print('A', end=' ')
                else:
                    print('.', end=' ')
            print()

    def update(self):
        head = self.snake[-1]
        if self.direction == 'right':
            new_head = (head[0] + 1, head[1])
        elif self.direction == 'left':
            new_head = (head[0] - 1, head[1])
        elif self.direction == 'up':
            new_head = (head[0], head[1] - 1)
        elif self.direction == 'down':
            new_head = (head[0], head[1] + 1)

        if (new_head[0] < 0 or new_head[0] >= self.width or
            new_head[1] < 0 or new_head[1] >= self.height or
            new_head in self.snake):
            return False

        self.snake.append(new_head)
        if self.apple == new_head:
            self.apple = self.generate_apple()
        else:
            self.snake.pop(0)

        return True

    def play(self):
        start_time = time.time()
        while time.time() - start_time < 10:
            self.display()
            if not self.update():
                break
            # Simple pathfinding to the apple
            head = self.snake[-1]
            if head[0] < self.apple[0]:
                self.direction = 'right'
            elif head[0] > self.apple[0]:
                self.direction = 'left'
            elif head[1] < self.apple[1]:
                self.direction = 'down'
            elif head[1] > self.apple[1]:
                self.direction = 'up'
            time.sleep(0.5)

if __name__ == '__main__':
    game = SnakeGame()
    game.play()