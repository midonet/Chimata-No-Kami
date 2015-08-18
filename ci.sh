#!/bin/bash

unset NODEPS; make clean; make distclean; make reboot; sleep 10; make

