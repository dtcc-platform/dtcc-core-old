set(LIBRARY generate_protobuf)

set(PROTO_SOURCE ${CMAKE_SOURCE_DIR}/dtcc-model/dtcc.proto )



# protobuf_generate_python(PROTO_PY ${PROTO_SOURCE} )
# add_custom_target(python_protobuf ALL DEPENDS ${PROTO_PY})
message("protopy output:  ${PROTO_PY}")

INSTALL(FILES ${PROTO_PY} DESTINATION ${CMAKE_SOURCE_DIR}/src/dtcc/)
link_libraries(dtccproto ${PROTOBUF_LIBRARY} Threads::Threads)
pybind11_add_module(${LIBRARY} cpp/${LIBRARY}.cpp)
set_target_properties(${LIBRARY} PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/src/dtcc/pblib)

#install(TARGETS ${PROTO_PY} DEFINITIONS ${CMAKE_SOURCE_DIR}/src/dtcc)

