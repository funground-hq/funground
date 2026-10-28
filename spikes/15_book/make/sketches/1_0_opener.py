import funground as f

f.size(600, 600)
f.background("oldlace")
f.no_stroke()
f.random_seed(3)
colors = ["tomato", "gold", "turquoise", "hotpink", "midnightblue"]
for i in range(36):
    f.fill(colors[i % 5])
    f.circle(f.random(600), f.random(600), f.random(30, 280))
f.fill("oldlace")
f.circle(300, 300, 170)
f.fill("tomato")
f.circle(300, 300, 100)
f.show()
