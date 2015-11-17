import sys
import time
import socket
import errno

from MyStrategy import MyStrategy
from RemoteProcessClient import RemoteProcessClient
from model.Move import Move

if sys.platform == 'win32':
    ERRNO_REFUSED = errno.WSAECONNREFUSED
    ERRNO_RESET = errno.WSAECONNRESET
else:
    ERRNO_REFUSED = errno.ECONNREFUSED
    ERRNO_RESET = errno.ECONNRESET

class Runner:
    def __init__(self):
        if sys.argv.__len__() == 4:
            self.remote_process_client = RemoteProcessClient(sys.argv[1], int(sys.argv[2]))
            self.token = sys.argv[3]
        else:
            for _ in xrange(20):
                try:
                    self.remote_process_client = RemoteProcessClient("127.0.0.1", 31001)
                except socket.error as ex:
                    if ex.errno == ERRNO_REFUSED:
                        time.sleep(0.1)
                        continue
                    raise
                else:
                    break
            self.token = "0000000000000000"

    def run(self):
        try:
            self.remote_process_client.write_token_message(self.token)
            team_size = self.remote_process_client.read_team_size_message()
            self.remote_process_client.write_protocol_version_message()
            game = self.remote_process_client.read_game_context_message()

            strategies = []

            for _ in xrange(team_size):
                strategies.append(MyStrategy())

            while True:
                player_context = self.remote_process_client.read_player_context_message()
                if player_context is None:
                    break

                player_cars = player_context.cars
                if player_cars is None or player_cars.__len__() != team_size:
                    break

                moves = []

                for car_index in xrange(team_size):
                    player_car = player_cars[car_index]

                    move = Move()
                    moves.append(move)
                    strategies[player_car.teammate_index].move(player_car, player_context.world, game, move)

                self.remote_process_client.write_moves_message(moves)
        except socket.error as ex:
            if ex.errno != ERRNO_RESET:
                raise
        except KeyboardInterrupt:
            pass
        finally:
            self.remote_process_client.close()


Runner().run()
