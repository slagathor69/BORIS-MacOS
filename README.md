BORIS (Behavioral Observation Research Interactive Software)
===============================================================
## Modified version of BORIS to work on MacOS
***This project is very much in an early development stage but can currently get latest BORIS version running natively on MacOS***

## Notes / caveats on macOS Support before installing

On Linux and Windows, BORIS embeds mpv directly into the Qt interface using the libmpv render API.

Unfortunately, on macOS this is not yet possible because:
- Apple does not provide native OpenGL beyond version 4.1, and is deprecating it in favor of Metal.
- mpv’s embedded render API (vo=libmpv) only supports OpenGL, not Vulkan or Metal.
- mpv’s newer GPU backends (vo=gpu, vo=gpu-next) do support Metal/Vulkan through libplacebo and MoltenVK, but those only work in mpv’s own floating window — they cannot currently be embedded inside a Qt widget.

Because of this limitation, this macOS version of BORIS uses a floating mpv window launched alongside the BORIS GUI. This allows full scoring and analysis functionality, but the video window is separate rather than integrated.
When upstream mpv (or libplacebo) adds Vulkan/Metal support to the render API, integration inside the Qt window on macOS may become possible.

Therefore the wrapper has mpv open alongside BORIS where you start video in mpv player then click back to BORIS window and score as usual. BORIS is aware of the floating mpv window and will keep track of appropriate time elapsed.

![Workflow example](preview.png)

A clunky workaround currently but I do not have the expertise yet to figure out how to get mpv integrated within BORIS Qt window. The creator of BORIS states that they do not have access to a Mac and are therefore unable to work on a native macOS version. This is my best effort so far.

***Any contributions are welcome. Feel free to fork this repository and add your own modifications. If you are able to get the video integrated and/or make this version a bit more polished, please let me know.*** 

*Additional note: there are some functions which will just throw error still i.e anything involving playback buttons in BORIS*

# How to install and run on MacOS

## 1) Install miniconda or anaconda according to https://www.anaconda.com/docs/getting-started/miniconda/main

## 2) Install homebrew if not already installed from https://brew.sh

## 3) Install mpv with Homebrew
`brew install --HEAD mpv`

## 4) Symlink libmpv to to /usr/local/lib
`sudo ln -s /opt/homebrew/lib/libmpv.dylib /usr/local/lib/libmpv.dylib`

***Why symlink?*** 
Python’s ctypes and many C-based Python packages like [mpv](https://pypi.org/project/mpv/) don’t use Homebrew’s paths (/opt/homebrew/lib) unless explicitly told to. Instead, they search system library paths such as:
	•	/usr/lib
	•	/usr/local/lib

So if libmpv.dylib is not in one of those default locations or specified in DYLD_LIBRARY_PATH, the dynamic linker fails to resolve it. Creating a symlink into /usr/local/lib ensures:
	•	ctypes.CDLL('libmpv.dylib') can find it.
	•	It works across restarts and environments without needing export DYLD_LIBRARY_PATH=….
	•	Python code using the mpv bindings initializes correctly.

I'm sure there is a better way of setting an environment variable but this is what I've done to get it working.

## 5) Clone this repository
`git clone https://github.com/slagathor69/BORIS-MacOS.git`

## 6) Create boris conda environment using yaml file
`conda env create -f boris.yaml`

## 7) Activate conda environment
`conda activate boris`

## 8) Start boris from repository directory using custom wrapper
`./run.sh`

***The wrapper ensures that mpv socket is established as well as setting numeric locale to "C" both of which BORIS requires to run***

![BORIS logo](https://github.com/olivierfriard/BORIS/blob/master/boris/icons/logo_boris.png?raw=true)

See the official [BORIS web site](https://www.boris.unito.it).


See the official [BORIS Github repository](https://github.com/olivierfriard/BORIS).


BORIS is an easy-to-use event logging software for video/audio coding or live observations.

BORIS is a free and open-source software available for GNU/Linux and Windows.
Alternative ways to run BORIS on MacOS using a VM [BORIS on MacOS with VM](https://www.boris.unito.it/download_mac).

It provides also some analysis tools like time budget and some plotting functions.

The BORIS paper has more than 2332 citations in peer-reviewed scientific publications.

# License

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

Distributed with a [GPL v.3 license](LICENSE.TXT).

Copyright (C) 2012-2025 Olivier Friard
