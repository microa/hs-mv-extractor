
<h1 align="center">
    <a href="https://github.com/LukasBommes/mv-extractor" target="blank_">
        <img width="250" alt="mvextractor" src="https://raw.githubusercontent.com/LukasBommes/mv-extractor/cb8e08f4c1e161d103d5382ded93134f26e96f05/logo.svg" />
    </a>
    <br>
    Motion Vector Extractor
</h1>

This tool extracts frames, motion vectors and frame types from H.264 and MPEG-4 Part 2 encoded videos.

This class is a replacement for OpenCV's [VideoCapture](https://docs.opencv.org/4.1.0/d8/dfe/classcv_1_1VideoCapture.html) and can be used to read and decode video frames from a H.264 or MPEG-4 Part 2 encoded video stream/file. It returns the following values for each frame:
- decoded frame as BGR image
- motion vectors
- Frame type (keyframe, P- or B-frame)

You can use these for applications, such as fast visual object tracking. Both a C++ and a Python API is provided. Under the hood [FFMPEG](https://github.com/FFmpeg/FFmpeg) is used.

The image below shows a video frame with extracted motion vectors overlaid.

![motion_vector_demo_image](https://raw.githubusercontent.com/LukasBommes/mv-extractor/cb8e08f4c1e161d103d5382ded93134f26e96f05/mvs.png)

A usage example can be found [here](https://github.com/LukasBommes/mv-extractor/blob/master/src/mvextractor/__main__.py).

*Note*: Versions 1.x of the mv-extractor additionally returned the timestamps of video frames. For RTSP streams the UTC wall time of the moment the sender sent out a frame was returned (as opposed to an easily retrievable timestamp for the frame reception). Since this feature required patching FFMPEG-internals it proved difficult to maintain. Hence, I decided to remove this feature in the 2.0 release. If you rely on this feature, please use version 1.1.0.

## News

### Recent Changes in Release 2.0.0

- New motion-vectors-only mode, in which frame decoding is skipped for better performance (thanks to [@microa](https://github.com/LukasBommes/mv-extractor/pull/78))
- Dropped extraction of timestamps as this feature was complex and difficult to maintain. Note the breaking API change to the `read` and `retrieve` methods of the `VideoCapture` class

```diff
- ret, frame, motion_vectors, frame_type, timestamp = cap.read()
+ ret, frame, motion_vectors, frame_type = cap.read()
```

- Added support for Python 3.13 and 3.14
- Moved installation of FFMPEG and OpenCV from script files directly into Dockerfile
- Improved quickstart section of the readme


## Quickstart

### Step 1: Install

```bash
pip install --upgrade pip
pip install motion-vector-extractor
```
Note, that we currently provide the package only for x86-64 linux, such as Ubuntu or Debian, and Python 3.9 to 3.14. If you are on a different platform, please use the Docker image as described [below](#installation-via-docker).

### Step 2: Extract Motion Vectors

You can follow along the examples below using the example video [`vid_h264.mp4`](https://github.com/LukasBommes/mv-extractor/blob/master/vid_h264.mp4) from the repo.

#### Command Line

```bash
# Extract motion vectors and show live preview
extract_mvs vid_h264.mp4 --preview --verbose

# Extract motion vectors and skip frame decoding (faster)
extract_mvs vid_h264.mp4 --verbose --skip-decoding-frames

# Extract and store motion vectors and frames to disk without showing live preview
extract_mvs vid_h264.mp4 --dump

# See all available options
extract_mvs -h
```

#### Python API
```python
from mvextractor.videocap import VideoCap

cap = VideoCap(decode_frames=True)
cap.open("vid_h264.mp4")

while True:
    ret, frame, motion_vectors, frame_type = cap.read()
    if not ret:
        break
    print(f"Motion vectors: {len(motion_vectors)}")
    print(f"Frame type: {frame_type}")
    print(f"Frame size: {frame.shape}")

cap.release()
```

## Advanced Usage

### Run Tests

You can run the test suite either directly on your machine or (easier) within the provided Docker container. Both methods require you to first clone the repository. To this end, change into the desired installation directory on your machine and run
```bash
git clone https://github.com/LukasBommes/mv-extractor.git mv_extractor
```

#### In Docker Container

To run the tests in the Docker container, change into the `mv_extractor` directory, and run
```bash
./run.sh /bin/bash -c 'yum install -y compat-openssl10 && python3.12 -m unittest discover -s tests -p "*tests.py"'
```

#### On Host

To run the tests directly on your machine, you need to install the motion vector extractor as explained [above](#step-1-install).

Now, change into the `mv_extractor` directory and run the tests with
```bash
python3.12 -m unittest discover -s tests -p "*tests.py"
```
Confirm that all tests pass.

Some tests run the [LIVE555 Media Server](http://www.live555.com/mediaServer/), which has dependencies on its own, such as OpenSSL. Make sure these dependencies are installed correctly on your machine, or otherwise you will get test failures with messages, such as "error while loading shared libraries: libssl.so.10: cannot open shared object file: No such file or directory". E.g. in Alma Linux you could fix this issue by installing OpenSSL with
```bash
yum install -y compat-openssl10
```
For other operating systems you may be lacking additional dependencies, and the package names and installation command may differ.

### Importing mvextractor into Your Own Scripts

If you want to use the motion vector extractor in your own Python script import it via
```python
from mvextractor.videocap import VideoCap
```
You can then use it according to the example in `extract_mvs.py`.

Generally, a video file is opened by `VideoCap.open()` and frames, motion vectors and frame types are read by calling `VideoCap.read()` repeatedly. Before exiting the program, the video file has to be closed by `VideoCap.release()`. For a more detailed explanation see the API documentation below.

### Installation via Docker

Instead of installing the motion vector extractor via PyPI you can also use the prebuild Docker image from [DockerHub](https://hub.docker.com/r/lubo1994/mv-extractor). The Docker image contains the motion vector extractor and all its dependencies and comes in handy for quick testing or in case your platform is not compatible with the provided Python package.

#### Prerequisites

To use the Docker image you need to install [Docker](https://docs.docker.com/). Furthermore, you need to clone the source code with
```bash
git clone https://github.com/LukasBommes/mv-extractor.git mv_extractor
```

#### Run Motion Vector Extraction in Docker

Afterwards, you can run the extraction script in the `mv_extractor` directory as follows
```bash
./run.sh python3.12 extract_mvs.py vid_h264.mp4 --preview --verbose
```
This pulls the prebuild Docker image from DockerHub and runs the extraction script inside the Docker container.

#### Building the Docker Image Locally (Optional)
 
This step is not required and for faster installation, we recommend using the prebuilt image.
If you still want to build the Docker image locally, you can do so by running the following command in the `mv_extractor` directory
```bash
docker build . --tag=mv-extractor
```
Note that building can take more than one hour.

Now, run the docker container with
```bash
docker run -it --ipc=host --env="DISPLAY" -v $(pwd):/home/video_cap -v /tmp/.X11-unix:/tmp/.X11-unix:rw mv-extractor /bin/bash
```


## Python API

This module provides a Python API which is very similar to that of OpenCV [VideoCapture](https://docs.opencv.org/4.1.0/d8/dfe/classcv_1_1VideoCapture.html). Using the Python API is the recommended way of using the H.264 Motion Vector Capture class.

#### Class :: VideoCap()

| Methods | Description |
| --- | --- |
| VideoCap() | Constructor |
| open() | Open a video file or url |
| grab() | Reads the next video frame and motion vectors from the stream |
| retrieve() | Decodes and returns the grabbed frame and motion vectors |
| read() | Convenience function which combines a call of grab() and retrieve() |
| release() | Close a video file or url and release all ressources |

| Attributes | Description |
| --- | --- |
| decode_frames | Getter to check if frame decoding is activated (True) or skipped (False) for this VideoCap instance |

##### Method :: VideoCap()

Constructor.

| Parameter | Type | Description |
| --- | --- | --- |
| decode_frames | bool | If True (default) RGB frames are decoded and returned in addition to extracted motion vectors. If False, frame decoding is skipped and only motion vectors are extracted and returned, yielding much higher extraction througput. |

##### Method :: open()

Open a video file or url. The stream must be H264 encoded. Otherwise, undesired behaviour is likely.

| Parameter | Type | Description |
| --- | --- | --- |
| url | string | Relative or fully specified file path or an url specifying the location of the video stream. Example "vid.flv" for a video file located in the same directory as the source files. Or "rtsp://xxx.xxx.xxx.xxx:554" for an IP camera streaming via RTSP. |

| Returns | Type | Description |
| --- | --- | --- |
| success | bool | True if video file or url could be opened successfully, false otherwise. |

##### Method :: grab()

Reads the next video frame and motion vectors from the stream, but does not yet decode it. Thus, grab() is fast. A subsequent call to retrieve() is needed to decode and return the frame and motion vectors. the purpose of splitting up grab() and retrieve() is to provide a means to capture frames in multi-camera scenarios which are as close in time as possible. To do so, first call grab() on all cameras and afterwards call retrieve() on all cameras.

Takes no input arguments.

| Returns | Type | Description |
| --- | --- | --- |
| success | bool | True if next frame and motion vectors could be grabbed successfully, false otherwise. |

##### Method :: retrieve()

Decodes and returns the grabbed frame and motion vectors. Prior to calling retrieve() on a stream, grab() needs to have been called and returned successfully.

Takes no input arguments and returns a tuple with the elements described in the table below.

| Index | Name | Type | Description |
| --- | --- | --- | --- |
| 0 | success | bool | True in case the frame and motion vectors could be retrieved sucessfully, false otherwise or in case the end of stream is reached. When false, the other tuple elements are set to empty numpy arrays or 0. |
| 1 | frame | numpy array | Array of dtype uint8 shape (h, w, 3) containing the decoded video frame. w and h are the width and height of this frame in pixels. Channels are in BGR order. If no frame could be decoded an empty numpy ndarray of shape (0, 0, 3) and dtype uint8 is returned. If the VideoCap instance was constructed with decode_frames=False None is returned instead. |
| 2 | motion vectors | numpy array | Array of dtype int32 and shape (N, 10) containing the N motion vectors of the frame. Each row of the array corresponds to one motion vector. If no motion vectors are present in a frame, e.g. if the frame is an `I` frame an empty numpy array of shape (0, 10) and dtype int32 is returned. The columns of each vector have the following meaning (also refer to [AVMotionVector](https://ffmpeg.org/doxygen/4.1/structAVMotionVector.html) in FFMPEG documentation): <br>- 0: `source`: offset of the reference frame from the current frame. The reference frame is the frame where the motion vector points to and where the corresponding macroblock comes from. If `source < 0`, the reference frame is in the past. For `source > 0` the it is in the future (in display order).<br>- 1: `w`: width of the vector's macroblock.<br>- 2: `h`: height of the vector's macroblock.<br>- 3: `src_x`: x-location (in pixels) where the motion vector points to in the reference frame.<br>- 4: `src_y`: y-location (in pixels) where the motion vector points to in the reference frame.<br>- 5: `dst_x`: x-location of the vector's origin in the current frame (in pixels). Corresponds to the x-center coordinate of the corresponding macroblock.<br>- 6: `dst_y`: y-location of the vector's origin in the current frame (in pixels). Corresponds to the y-center coordinate of the corresponding macroblock.<br>- 7: `motion_x`: Macroblock displacement in x-direction, multiplied by `motion_scale` to become integer. Used to compute fractional value for `src_x` as `src_x = dst_x + motion_x / motion_scale`.<br>- 8: `motion_y`: Macroblock displacement in y-direction, multiplied by `motion_scale` to become integer. Used to compute fractional value for `src_y` as `src_y = dst_y + motion_y / motion_scale`.<br>- 9: `motion_scale`: see definiton of columns 7 and 8. Used to scale up the motion components to integer values. E.g. if `motion_scale = 4`, motion components can be integer values but encode a float with 1/4 pixel precision.<br><br>Note: `src_x` and `src_y` are only in integer resolution. They are contained in the [AVMotionVector](https://ffmpeg.org/doxygen/4.1/structAVMotionVector.html) struct and exported only for the sake of completeness. Use equations in field 7 and 8 to get more accurate fractional values for `src_x` and `src_y`. |
| 3 | frame_type | string | Unicode string representing the type of frame. Can be `"I"` for a keyframe, `"P"` for a frame with references to only past frames and `"B"` for a frame with references to both past and future frames. A `"?"` string indicates an unknown frame type. |

##### Method :: read()

Convenience function which internally calls first grab() and then retrieve(). It takes no arguments and returns the same values as retrieve().

##### Method :: release()

Close a video file or url and release all ressources. Takes no input arguments and returns nothing.


## C++ API

The C++ API differs from the Python API in what parameters the methods expect and what values they return. Refer to the docstrings in `src/video_cap.hpp`.


## Theory

What follows is a short explanation of the data returned by the `VideoCap` class. Also refer this [excellent book](https://dl.acm.org/citation.cfm?id=1942939) by Iain E. Richardson for more details.

##### Frame
The decoded video frame. Nothing special about that.

##### Motion Vectors

H.264 and MPEG-4 Part 2 use different techniques to reduce the size of a raw video frame prior to sending it over a network or storing it into a file. One of those techniques is motion estimation and prediction of future frames based on previous or future frames. Each frame is segmented into macroblocks of e.g. 16 pixel x 16 pixel. During encoding motion estimation matches every macroblock to a similar looking macroblock in a previously encoded frame (note that this frame can also be a future frame since encoding and presentation order might differ). This allows to transmit only those motion vectors and the reference macroblock instead of all macroblocks, effectively reducing the amount of transmitted or stored data. <br>
Motion vectors correlate directly with motion in the video scene and are useful for various computer vision tasks, such as visual object tracking.

In MPEG-4 Part 2 macroblocks are always 16 pixel x 16 pixel. In H.264 macroblocks can be 16x16, 16x8, 8x16, 8x8, 8x4, 4x8, or 4x4 in size.

##### Frame Types

The frame type is either "P", "B" or "I" and refers to the H.264 encoding mode of the current frame. An "I" frame is send fully over the network and serves as a reference for "P" and "B" frames for which only differences to previously decoded frames are transmitted. Those differences are encoded via motion vectors. As a consequence, for an "I" frame no motion vectors are returned by this library. The difference between "P" and "B" frames is that "P" frames refer only to past frames, whereas "B" frames have motion vectors which refer to both past and future frames. References to future frames are possible even with live streams because the decoding order of frames differs from the presentation order.


## About

This software is written by [**Lukas Bommes**](https://lukasbommes.de/).
It is based on [MV-Tractus](https://github.com/jishnujayakumar/MV-Tractus/tree/master/include) and OpenCV's [videoio module](https://github.com/opencv/opencv/tree/master/modules/videoio).


#### License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/LukasBommes/mv-extractor/blob/master/LICENSE) file for details.


#### Citation

If you use our work for academic research please cite

```
@INPROCEEDINGS{9248145,
  author={L. {Bommes} and X. {Lin} and J. {Zhou}},
  booktitle={2020 15th IEEE Conference on Industrial Electronics and Applications (ICIEA)}, 
  title={MVmed: Fast Multi-Object Tracking in the Compressed Domain}, 
  year={2020},
  volume={},
  number={},
  pages={1419-1424},
  doi={10.1109/ICIEA48937.2020.9248145}}
```


