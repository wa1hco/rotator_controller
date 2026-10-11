# Include paths adjusted for the software/sim/ layout in rotator_controller.
# Upstream: wa1hco/k3ng_rotator_controller @ 27156ad04ab3bf05b93761b5a9612c2a382143ac

CXX := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -I. -I..

TEST_SOURCES := test_main.cpp test_feature_config.cpp test_rotator_simulator.cpp test_rotator_protocol_shim.cpp \
	../rotator_feature_config.cpp \
	../rotator_simulator.cpp \
	../rotator_protocol_shim.cpp
TEST_BINARY := run_tests

INTEGRATION_SOURCES := test_main.cpp test_k3ng_integration.cpp
INTEGRATION_BINARY  := run_integration_tests

.PHONY: test integration clean

test: $(TEST_BINARY)
	./$(TEST_BINARY)

integration: $(INTEGRATION_BINARY)
	./$(INTEGRATION_BINARY)

$(TEST_BINARY): $(TEST_SOURCES)
	$(CXX) $(CXXFLAGS) $(TEST_SOURCES) -o $(TEST_BINARY)

$(INTEGRATION_BINARY): $(INTEGRATION_SOURCES)
	$(CXX) $(CXXFLAGS) $(INTEGRATION_SOURCES) -o $(INTEGRATION_BINARY)

clean:
	rm -f $(TEST_BINARY) $(INTEGRATION_BINARY)
