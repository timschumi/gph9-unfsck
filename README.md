# gph9-unfsck

Recover files in case your microSD card got corrupted and/or accidentally
quick-formatted.

Note that this has only been tested with a GoPro Hero 9 that is recording to
an exFAT filesystem.

As of now, the tool assumes that the FAT is largely intact and that the
filesystem metrics haven't changed from when the files were originally
recorded. There are opportunities for the tool to detect whether the current
metrics make sense and to puzzle together files that are not in the FAT and
not too fragmented, but neither of these things are implemented currently.
