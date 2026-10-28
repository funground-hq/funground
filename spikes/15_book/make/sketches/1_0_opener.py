import funground as f

f.size(600, 600)
f.background("oldlace")
f.no_stroke()
f.random_seed(3)
# colour, across, down, width: the big shapes first, the small ones on top
shapes = [("gold", 190, 170, 230), ("turquoise", 400, 430, 270), ("hotpink", 480, 130, 100),
          ("midnightblue", 110, 450, 80), ("tomato", 300, 300, 160), ("oldlace", 300, 300, 56),
          ("gold", 490, 300, 44), ("hotpink", 190, 520, 44)]
for color, x, y, d in shapes:
    f.fill(color)
    f.circle(x + f.random(-10, 10), y + f.random(-10, 10), d)
f.show()
