    puts(green("configuring midonet virtual switch (using cli on %s)" % env.host_string))

    run("""

midonet-cli -e 'bridge list' | grep 'name alexbridge' || midonet-cli -e 'bridge add name alexbridge'

""")

