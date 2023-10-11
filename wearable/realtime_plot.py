import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.animation import FuncAnimation


def _log_to_animated_graph(i):
    file_name = 'belt_raw_data_prova.csv'
    col_names = ['time','gen_time', 'acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y', 'gyro_z', 'comp_x', 'comp_y', 'comp_z']
    data = pd.read_csv(file_name, parse_dates=True, index_col=0, names=col_names)
    data = data.iloc[-64:]

    plt.cla()
    plt.plot(data.index, data['acc_x'], label='Acc')
    plt.legend(loc='upper left')
    plt.tight_layout()


if __name__ == '__main__':
    anim = FuncAnimation(plt.gcf(), _log_to_animated_graph, interval=100)
    plt.show()