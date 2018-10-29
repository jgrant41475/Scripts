from pandas import ExcelFile
from os import scandir
import matplotlib.pyplot as plt
import numpy as np


info_path = "C:/Users/johng/Downloads/info/"
all_times = []

def autolabel(rects, ax):
    (y_bottom, y_top) = ax.get_ylim()
    y_height = y_top - y_bottom

    for rect in rects:
        height = rect.get_height()
        p_height = (height / y_height)
        if p_height > 0.95:
            label_position = height - (y_height * 0.05)
        else:
            label_position = height + (y_height * 0.01)
        if int(height) > 0:
            ax.text(rect.get_x() + rect.get_width()/2., label_position, '%d' % int(height), ha='center', va='bottom')

with scandir(info_path) as dir:
    for file in dir:
        book = ExcelFile(info_path + file.name)
        sheet = book.parse(book.sheet_names[0], header=None)

        x = range(24)
        times = [x for x in map(lambda x: x.hour, [x[0] for x in sheet.filter(items=[2])[3:].values])]
        freq = [y for y in map(lambda x: times.count(x), range(0,24))]

        fig, ax = plt.subplots()
        rects = ax.bar(x, freq, align="center", alpha=0.5)

        ax.set_ylim(0, max(freq)+1)
        ax.set_ylabel('# of Chats')
        ax.set_title(file.name)
        ax.set_xticks(np.arange(min(x), max(x)+1, 1.0))
        ax.set_xticklabels((["{}".format(x) for x in range(24)]))

        all_times.append(freq)
        print(freq)

        autolabel(rects, ax)
        plt.savefig("C:/users/johng/desktop/Reports/{}.png".format(file.name))
        plt.close()


x = range(24)
freq = list(map(lambda x: np.squeeze(np.asarray(np.matrix(all_times).sum(axis=0))), range(24)))[0]

fig, ax = plt.subplots()
rects1 = ax.bar(x, freq, align="center", alpha=0.5)

ax.set_ylim(0, max(freq)+1)
ax.set_ylabel('# of Chats')
ax.set_title('All Chats')
ax.set_xticks(np.arange(min(x), max(x)+1, 1.0))
ax.set_xticklabels((["{}".format(x) for x in range(24)]))

[print("{} = {} chats".format(x, freq[x])) for x in range(24)]
print("Total # of chats: {}".format(sum(freq)))

autolabel(rects1, ax)

plt.savefig("C:/users/johng/desktop/Reports/All_Chats.png")
plt.close()
