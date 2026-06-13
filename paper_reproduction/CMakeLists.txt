cmake_minimum_required(VERSION 3.0.2)
project(paper_reproduction)

find_package(catkin REQUIRED COMPONENTS rospy)

catkin_package(
  CATKIN_DEPENDS rospy
)

catkin_install_python(PROGRAMS
  scripts/gp_mpc_repro_node.py
  scripts/reference_publisher_repro_node.py
  scripts/letter_ref_publisher_node.py
  scripts/run_single_trial.py
  scripts/summarize_results.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config matlab
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)

install(DIRECTORY scripts/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/scripts
  USE_SOURCE_PERMISSIONS
  PATTERN "*.py" EXCLUDE
)

install(FILES README.md QUICKSTART.md
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
