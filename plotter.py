import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
 
objects = (["{}".format(x) for x in range(0,24)])
y_pos = np.arange(len(objects))
performance = [y for y in map(lambda x: data.count(x), set(data))]
 
plt.bar(y_pos, performance, align='center', alpha=0.5)
plt.xticks(y_pos, objects)
plt.ylabel('Frequency')
plt.title('Report')
 
plt.show()