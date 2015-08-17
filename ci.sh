#!/bin/bash

unset NODEPS; make distclean; make reboot; sleep 10; make

