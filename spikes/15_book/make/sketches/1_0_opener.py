import funground as f

f.size(600, 600)
f.background("oldlace")
f.no_stroke()
f.random_seed(3)
colors = ["tomato", "gold", "turquoise", "hotpink", "midnightblue"]
for i in range(36):
    f.fill(colors[i % 5])
    f.circle(at="random", size=f.random(30, 280))
f.fill("oldlace")
f.circle(size=170)
f.fill("tomato")
f.circle(size=100)
f.show()
