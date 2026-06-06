"""Tests for Ecology Engine."""
from src.ecology_engine import EcologyEngine, classify_niche


class TestNiche:
    def test_producer(self):
        assert classify_niche(energy_gen=10, energy_con=5, remnant_ratio=0) == "producer"
    def test_consumer(self):
        assert classify_niche(energy_gen=5, energy_con=10, remnant_ratio=0) == "consumer"
    def test_decomposer(self):
        assert classify_niche(energy_gen=5, energy_con=5, remnant_ratio=0.6) == "decomposer"


class TestEcologyEngine:
    def test_empty_scan(self):
        eng = EcologyEngine()
        net = eng.scan([], None)
        assert len(net.nodes) == 0 and len(net.edges) == 0

    def test_detect_competition(self):
        eng = EcologyEngine()
        structs = [
            {"id": "s1", "cells": {(5,5),(6,5),(7,5)}, "primary_type": 1, "age": 30},
            {"id": "s2", "cells": {(6,5),(7,5),(8,5)}, "primary_type": 1, "age": 30},
        ]
        net = eng.scan(structs, None)
        assert any(e.relationship == "competition" for e in net.edges)

    def test_detect_mutualism(self):
        eng = EcologyEngine()
        structs = [
            {"id": "s1", "cells": {(5,5),(5,6)}, "primary_type": 1, "age": 200},
            {"id": "s2", "cells": {(6,5),(6,6)}, "primary_type": 2, "age": 200},
        ]
        net = eng.scan(structs, None)
        assert any(e.relationship == "mutualism" for e in net.edges)
