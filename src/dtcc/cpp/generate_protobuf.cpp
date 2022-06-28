#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "protobuf/dtcc.pb.h"
#include "protobuf/include/VectorMethods.h"
#include "protobuf/include/BoundingBoxMethods.h"

namespace py = pybind11;
using namespace DTCC;

std::string hello()
{
  return "Hello World!";
}

int add(int i, int j) {
    return i + j;
}

py::bytes PBPointCloud(py::array_t<double> pts)
{
  auto pts_r = pts.unchecked<2>();
  std::vector<Vector3D> pb_pts;
  size_t pt_count = pts_r.shape(0);
  PointCloud pc;
  for (size_t i = 0 ; i < pt_count ; i++)
  {
    auto v3d = DTCC::Vector(pts_r(i,0),pts_r(i,1),pts_r(i,2));
    pb_pts.push_back(v3d);
  }
  google::protobuf::RepeatedPtrField<Vector3D> pt_data(pb_pts.begin(), pb_pts.end());
  pc.mutable_points()->Swap(&pt_data);
  std::string pbString;
  pc.SerializeToString(&pbString);

  return py::bytes(pbString);
}



PYBIND11_MODULE(generate_protobuf, m) {
    m.doc() = "generate protobufs of various models"; // optional module docstring

    m.def("add", &add, "A function that adds two numbers");
    m.def("hello", &hello, "Hello World");
    m.def("PBPointCloud", &PBPointCloud, "Generate PB Pointcloud object");
}