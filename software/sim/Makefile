# Include paths adjusted for the software/sim/ layout in rotator_controller.
# Upstream: wa1hco/k3ng_rotator_controller @ 27156ad04ab3bf05b93761b5a9612c2a382143ac
# (these sources lived in k3ng_rotator_controller/ and simulator/).

CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -I.

SIM_SOURCES := pc_rotator_sim.cpp rotator_simulator.cpp rotator_protocol_shim.cpp
SIM_BINARY := pc_rotator_sim

GUI_SOURCES := gui_server.cpp
GUI_BINARY := gui_server

.PHONY: build run gui gui-run test clean

build: $(SIM_BINARY) $(GUI_BINARY)

run: $(SIM_BINARY)
	./$(SIM_BINARY)

gui: $(GUI_BINARY)

gui-run: $(GUI_BINARY)
	./$(GUI_BINARY)

test:
	$(MAKE) -C tests test

$(SIM_BINARY): $(SIM_SOURCES) rotator_simulator.h rotator_protocol_shim.h
	$(CXX) $(CXXFLAGS) $(SIM_SOURCES) -o $(SIM_BINARY)

$(GUI_BINARY): $(GUI_SOURCES)
	$(CXX) $(CXXFLAGS) $(GUI_SOURCES) -o $(GUI_BINARY)

clean:
	rm -f $(SIM_BINARY) $(GUI_BINARY)
	$(MAKE) -C tests clean
