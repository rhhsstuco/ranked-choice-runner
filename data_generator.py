import random

pres = ["Alan Turing", "Grace Hopper", "Bjarne Stroustrup", "Ada Lovelace"]
vice_pres = ["Leonhard Euler", "Hypatia"]
secretary = ["Albert Einstein", "Marie Curie", "Srinivasa Ramanujan"]

with open("data.csv", "w") as f:
    f.write("time,President (1),President (2),President (3),President (4),Vice President,Secretary (1),Secretary (2),"
            "Secretary (3)\n")

    for _ in range(2000):
        row = ["time"]
        random.shuffle(pres)
        row.extend(pres)

        row.append(random.choice(vice_pres))

        random.shuffle(secretary)
        row.extend(secretary)

        f.write(",".join(row))
        f.write("\n")
