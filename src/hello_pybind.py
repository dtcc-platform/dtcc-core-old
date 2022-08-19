from dtcc.pointCloud import loadLAS

pb_las = loadLAS("../data/10A005_617_38_5050.laz")
with open("../data/pb_las.pb",'wb') as dst:
    dst.write(pb_las)
  