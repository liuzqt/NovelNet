# encoding: utf-8

'''

@author: David


@file: graph.py

@time: 23:25 

@desc:
'''

def main():
    with open("relationship.txt", "r") as f:
        lines = f.readlines()
    fro = -1
    tos = []
    chardict = {}
    results = []
    for l in lines:
        if l.startswith("======"):
            for t in tos:
                if fro != -1:
                    results.append(str(fro) + " " + str(t))
            fro = -1
            tos = []
            continue
        if fro == -1:
            try:
                fro = int(l.split("\t")[0])
            except:
                fro = int(l.split("\t")[0].strip().__hash__()) % 43571

            chardict[fro] = l.split("\t")[1].strip()
            continue

        if l.startswith("-------"):
            continue
        if int(l.split("\t")[2]) > 3:
            try:
                tos.append(int(l.split("\t")[0]))
            except:
                tos.append(int(l.split("\t")[0].strip().__hash__()) % 43571)
    return results, chardict

if __name__ == '__main__':
    r = main()
    #ls = [str(i) + ": " + str(r[1][i]) for i in r[1]]
    test = [[81, 2, 155, 20, 39, 154, 123], [193, 71, 96, 74, 12, 124, 37, 27168, 165, 15657, 113, 117, 120, 191, 188, 189, 190, 63], [104, 107, 77, 150, 87], [67, 16548, 168, 139, 108, 75, 36, 95], [129, 3, 5, 23882, 11281, 146, 147, 85, 28, 98, 41, 43, 45, 46, 83, 60], [32, 130, 132, 17416, 35020, 66, 142, 141, 178, 79, 158], [131, 6, 15, 88, 90, 27, 30, 102, 167, 105, 42, 174, 176, 114, 116, 118, 122, 33851], [148, 69, 86, 72, 11, 94], [68, 93, 73, 173, 78, 61, 144, 19, 52, 149, 24119, 143, 29], [177, 115, 84, 70, 135, 8], [64, 1280, 133, 1, 136, 16, 17, 1557, 156, 157, 163, 164, 38, 9585, 47, 48, 49, 56], [0, 128, 97, 10, 76, 13, 23, 25, 26, 33, 20774, 166, 175, 112, 51, 57, 125], [192, 160, 162, 4, 161, 40, 109, 110, 152, 119, 24, 153, 58, 32625], [44, 92, 13174, 55], [21875, 103, 186, 187, 151, 41114], [65, 194, 35, 100, 101, 14, 82, 59], [134, 7, 169, 106, 171, 179, 180, 181, 54, 121, 170, 53], [145, 126, 398, 62, 111], [6617, 99, 2389, 140, 80, 18, 21, 182, 183, 185, 91, 159, 31]]
    print(r[1])
    with open("adj.txt","w") as f:
        f.write("\n".join(r[0]))
    with open("temp.txt","w") as f:
        for t in test:
            for c in t:
                try:
                    f.write(r[1][c])
                except:
                    f.write(str(c))
            f.write('\n')

