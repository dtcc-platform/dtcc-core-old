#include <math.h>    
#include <limits>

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "protobuf/dtcc.pb.h"
#include "protobuf/include/VectorMethods.h"
#include "protobuf/include/BoundingBoxMethods.h"

namespace py = pybind11;
using namespace DTCC;

py::bytes PBPointCloud(py::array_t<double> pts,
                       py::array_t<u_int8_t> classification,
                       py::array_t<u_int16_t> intensity,
                       py::array_t<u_int8_t> returnNumber,
                       py::array_t<u_int8_t> numberOfReturns)
{
  auto pts_r = pts.unchecked<2>();
  auto class_r = classification.unchecked<1>();
  auto intensity_r = intensity.unchecked<1>();
  auto retNr_r = returnNumber.unchecked<1>();
  auto numReturn_r = numberOfReturns.unchecked<1>();

  std::vector<Vector3D> pb_pts;
  size_t pt_count = pts_r.shape(0);

  PointCloud pc;
  for (size_t i = 0; i < pt_count; i++)
  {
    auto v3d = DTCC::Vector(pts_r(i, 0), pts_r(i, 1), pts_r(i, 2));
    pb_pts.push_back(v3d);
  }
  google::protobuf::RepeatedPtrField<Vector3D> pt_data(pb_pts.begin(), pb_pts.end());
  pc.mutable_points()->Swap(&pt_data);

  size_t num_classes = class_r.shape(0);
  if (num_classes > 0)
  {
    google::protobuf::RepeatedField<uint32_t> cls_data;
    for (size_t i = 0; i < num_classes; i++)
    {
      cls_data.Add(class_r(i));
    }
    pc.mutable_classification()->Swap(&cls_data);
  }

  size_t num_intensity = intensity_r.shape(0);
  if (num_intensity > 0)
  {
    google::protobuf::RepeatedField<uint32_t> int_data;
    for (size_t i = 0; i < num_intensity; i++)
    {
      int_data.Add(intensity_r(i));
    }
    pc.mutable_intensity()->Swap(&int_data);
  }

  size_t num_retnr = retNr_r.shape(0);
  if (num_retnr > 0)
  {
    google::protobuf::RepeatedField<uint32_t> retnr_data;
    for (size_t i = 0; i < num_retnr; i++)
    {
      retnr_data.Add(retNr_r(i));
    }
    pc.mutable_returnnumber()->Swap(&retnr_data);
  }

  size_t num_numret = numReturn_r.shape(0);
  if (num_numret > 0)
  {
    google::protobuf::RepeatedField<uint32_t> numret_data;
    for (size_t i = 0; i < num_numret; i++)
    {
      numret_data.Add(numReturn_r(i));
    }
    pc.mutable_numreturns()->Swap(&numret_data);
  }

  std::string pbString;
  pc.SerializeToString(&pbString);

  return py::bytes(pbString);
}


py::bytes PBCompactPointCloud(py::array_t<double> pts,
                              py::array_t<u_int8_t> classification,
                              py::array_t<u_int16_t> intensity,
                              py::array_t<u_int8_t> returnNumber,
                              py::array_t<u_int8_t> numberOfReturns)
{
  auto pts_r = pts.unchecked<2>();
  auto class_r = classification.unchecked<1>();
  auto intensity_r = intensity.unchecked<1>();
  auto retNr_r = returnNumber.unchecked<1>();
  auto numReturn_r = numberOfReturns.unchecked<1>();
  size_t pt_count = pts_r.shape(0);

  bool has_class = class_r.shape(0) > 0;
  bool has_intensity = intensity_r.shape(0) > 0;
  bool has_returns = (retNr_r.shape(0) > 0 && numReturn_r.shape(0) > 0);
  bool has_metadata = has_class || has_intensity || has_returns;

  google::protobuf::RepeatedField<int32_t> x_pt;
  google::protobuf::RepeatedField<int32_t> y_pt;
  google::protobuf::RepeatedField<int32_t> z_pt;  
  google::protobuf::RepeatedField<uint32_t> metadata;  

  

  float x, y, z;
  float x_min, x_max, y_min, y_max, z_min, z_max;
  x_min = y_min = z_min = std::numeric_limits<float>::max();
  x_max = y_max = z_max = std::numeric_limits<float>::min();
  for (size_t i = 0; i < pt_count; i++)
  {
    x = pts_r(i, 0);
    x_min = x<x_min ? x : x_min;
    x_max = x>x_max ? x : x_max;

    y = pts_r(i, 1);
    y_min = y<y_min ? y : y_min;
    y_max = y>y_max ? y : y_max;

    z = pts_r(i, 2);
    z_min = z<z_min ? z : z_min;
    z_max = x>z_max ? x : z_max;
  }

  // TODO? Replace this with true median
  float x_offset = x_min + ((x_max - x_min) / 2);
  float y_offset = y_min + ((y_max - y_min) / 2);
  float z_offset = z_min + ((z_max - z_min) / 2);

  // TODO calclulate based on range and accuracy
  float x_scale = 0.001;
  float y_scale = 0.001;
  float z_scale = 0.001;

  uint16_t intensityNr;
  uint8_t classificationNr;
  uint8_t scanNr;
  uint32_t metadataNr;
  
  for (size_t i = 0; i < pt_count; i++)
  {
    x_pt.Add( lround((pts_r(i, 0)-x_offset) / x_scale ));
    y_pt.Add( lround((pts_r(i, 1)-y_offset) / y_scale ));
    z_pt.Add( lround((pts_r(i, 2)-z_offset) / z_scale ));
    if (has_metadata)
    {
      intensityNr = 0;
      classificationNr = 0;
      scanNr = 0;
      metadataNr = 0;
      if (has_class)
        classificationNr = class_r(i);
      if (has_intensity)
        intensityNr = intensity_r(i);
      if (has_returns)
      {
        uint8_t retn = retNr_r(i);
        uint8_t nret = numReturn_r(i);
        scanNr = (retn & 7) | ((nret & 7) << 3);
      } 
      metadataNr |= intensityNr;
      metadataNr |= (classificationNr << 16);
      metadataNr |= (scanNr << 24);
      metadata.Add(metadataNr);

    }



  }

  CompactPointCloud pc;
  pc.mutable_x()->Swap(&x_pt);
  pc.mutable_y()->Swap(&y_pt);
  pc.mutable_z()->Swap(&z_pt);
  if (has_metadata)
    pc.mutable_metadata()->Swap(&metadata);

  std::string pbString;
  pc.SerializeToString(&pbString);

  return py::bytes(pbString);
}

PYBIND11_MODULE(generate_protobuf, m)
{
  m.doc() = "generate protobufs of various models"; // optional module docstring
  m.def("PBPointCloud", &PBPointCloud, "Generate PB Pointcloud object");
  m.def("PBCompatcPointCloud", &PBCompactPointCloud, "Generate a PB Pointcloud that's smaller, but harder to parse");
}