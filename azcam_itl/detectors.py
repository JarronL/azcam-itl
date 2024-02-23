# Database entries for detectors.

detector_ccd57 = {
    "name": "CCD57",
    "description": "e2v CCD57",
    "ref_pixel": [256, 256],
    # "format": [560, 24, 0, 0, 528, 14, 0, 0, 528],
    "format": [536, 12, 0, 0, 528, 14, 0, 0, 528],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 512, 1, 512, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

detector_ccid21 = {
    "name": "CCID21",
    "description": "MIT-LL CCID21",
    "ref_pixel": [256, 256],
    "format": [512, 4, 0, 0, 512, 0, 0, 0, 512],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 512, 1, 512, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

detector_ccid37 = {
    "name": "CCID37",
    "description": "MIT-LL CCID37",
    "ref_pixel": [256, 256],
    "format": [512, 4, 0, 0, 512, 0, 0, 0, 512],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 512, 1, 512, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

detector_512ft = {
    "name": "512ft",
    "description": "UA foundry 512FT CCD",
    "ref_pixel": [256, 256],
    "format": [512, 4, 0, 0, 512, 0, 0, 0, 512],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 512, 1, 512, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

detector_sta0510 = {
    "name": "STA0510",
    "description": "STA STA0510 CCD",
    "ref_pixel": [600, 400],
    "format": [1200, 18, 0, 20, 800, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 1200, 1, 800, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

detector_sta3600 = {
    "name": "STA3600",
    "description": "STA STA3600 CCD",
    "ref_pixel": [1032, 1032],
    "format": [2064, 12, 0, 20, 2064, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 2, [0, 3]],
    "roi": [1, 2064, 1, 2064, 1, 1],
    "ext_position": [[1, 1], [1, 2]],
    "jpg_order": [1, 2],
}

detector_sta3600_VIRUS2 = {
    "name": "STA3600",
    "description": "STA STA3600 CCD",
    "ref_pixel": [1032, 1032],
    "format": [2064, 12, 0, 20, 2064, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 2064, 1, 2064, 1, 1],
}

detector_sta3800 = {
    "name": "STA3800",
    "description": "STA STA3800 CCD",
    "ref_pixel": [2036, 2000],
    "format": [509 * 8, 4, 0, 50, 2000 * 2, 0, 0, 10, 0],
    "focalplane": [1, 1, 8, 2, [0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2]],
    "roi": [1, 4072, 1, 4000, 1, 1],
    "ext_position": [
        [8, 1],
        [7, 1],
        [6, 1],
        [5, 1],
        [4, 1],
        [3, 1],
        [2, 1],
        [1, 1],
        [1, 2],
        [2, 2],
        [3, 2],
        [4, 2],
        [5, 2],
        [6, 2],
        [7, 2],
        [8, 2],
    ],
    "ext_number": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    "jpg_order": [8, 7, 6, 5, 4, 3, 2, 1, 9, 10, 11, 12, 13, 14, 15, 16],
    "det_number": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [5, 1],
        [6, 1],
        [7, 1],
        [8, 1],
        [1, 2],
        [2, 2],
        [3, 2],
        [4, 2],
        [5, 2],
        [6, 2],
        [7, 2],
        [8, 2],
    ],
    "amp_pixel_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "ext_name": [
        "im1",
        "im2",
        "im3",
        "im4",
        "im5",
        "im6",
        "im7",
        "im8",
        "im9",
        "im10",
        "im11",
        "im12",
        "im13",
        "im14",
        "im15",
        "im16",
    ],
}

detector_sta4400 = {
    "name": "STA4400",
    "description": "STA STA4400 CCD",
    "ref_pixel": [2036, 1000],
    "format": [509 * 8, 4, 0, 50, 2000, 0, 0, 10, 0],
    "focalplane": [1, 1, 8, 1, [0, 0, 0, 0, 0, 0, 0, 0]],
    "roi": [1, 4072, 1, 2000, 1, 1],
    "ext_position": [
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [5, 1],
        [6, 1],
        [7, 1],
        [8, 1],
    ],
    "ext_number": [1, 2, 3, 4, 5, 6, 7, 8],
    "jpg_order": [1, 2, 3, 4, 5, 6, 7, 8],
    "det_number": [1, 1, 1, 1, 1, 1, 1, 1],
    "det_position": [[1, 1], [1, 1], [1, 1], [1, 1], [1, 1], [1, 1], [1, 1], [1, 1]],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [[1, 1], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1], [7, 1], [8, 1]],
    "amp_pixel_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "ext_name": ["im1", "im2", "im3", "im4", "im5", "im6", "im7", "im8"],
}

detector_sta1600 = {
    "name": "STA1600",
    "description": "STA STA1600LN CCD",
    "ref_pixel": [5280, 5280],
    "format": [10560, 11, 0, 50, 10560, 0, 0, 50, 0],
    "focalplane": [1, 1, 8, 2, [0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2]],
    "roi": [1, 10560, 1, 10560, 1, 1],
    "ext_position": [
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [5, 1],
        [6, 1],
        [7, 1],
        [8, 1],
        [1, 2],
        [2, 2],
        [3, 2],
        [4, 2],
        [5, 2],
        [6, 2],
        [7, 2],
        [8, 2],
    ],
    "ext_name": [
        "im1",
        "im2",
        "im3",
        "im4",
        "im5",
        "im6",
        "im7",
        "im8",
        "im9",
        "im10",
        "im11",
        "im12",
        "im13",
        "im14",
        "im15",
        "im16",
    ],
    "ext_number": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    "jpg_order": [8, 7, 6, 5, 4, 3, 2, 1, 9, 10, 11, 12, 13, 14, 15, 16],
    "det_number": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
        [3, 1],
        [4, 1],
        [5, 1],
        [6, 1],
        [7, 1],
        [8, 1],
        [1, 2],
        [2, 2],
        [3, 2],
        [4, 2],
        [5, 2],
        [6, 2],
        [7, 2],
        [8, 2],
    ],
    "amp_pixel_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
}

detector_sta4150_2amp_top = {
    "name": "STA41500",
    "description": "STA STA4150 CCD 2-amp mode",
    "ref_pixel": [2048, 2048],
    "format": [4096, 4, 0, 20, 4096, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 1, [0, 1]],
    "roi": [1, 4096, 1, 4096, 1, 1],
    "ext_position": [[1, 1], [2, 1]],
    "jpg_order": [1, 2],
}

detector_sta4150_2amp_left = {
    "name": "STA41500",
    "description": "STA STA4150 CCD 2-amp mode",
    "ref_pixel": [2048, 2048],
    "format": [4096, 4, 0, 20, 4096, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 2, [0, 2]],
    "roi": [1, 4096, 1, 4096, 1, 1],
    "ext_position": [[1, 1], [1, 2]],
    "jpg_order": [1, 2],
}

detector_sta4150_4amp = {
    "name": "STA4150",
    "description": "STA STA4150 CCD",
    "ref_pixel": [2048, 2048],
    "format": [4096, 4, 0, 20, 4096, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 2, [0, 1, 2, 3]],
    "amp_cfg": [0, 1, 2, 3],  # fixme
    "roi": [1, 4096, 1, 4096, 1, 1],
    "ext_position": [[1, 1], [2, 1], [1, 2], [2, 2]],
    "ext_number": [1, 2, 3, 4],
    "jpg_order": [1, 2, 3, 4],
    "det_number": [1, 1, 1, 1],
    "det_position": [[1, 1], [1, 1], [1, 1], [1, 1]],
    "det_gap": [[0.0, 0.0], [0.0, 0.0], [0.0, 0.0], [0.0, 0.0]],
    "amp_position": [[1, 1], [2, 1], [3, 1], [4, 1]],
    "amp_pixel_position": [
        [1, 1],
        [4096, 1],
        [1, 4096],
        [4096, 1],
    ],
    "ext_name": ["im1", "im2", "im3", "im4"],
}

detector_qhy174 = {
    "name": "QHY174",
    "description": "QHY174 CMOS camera",
    "ref_pixel": [960, 600],
    "format": [1920, 0, 0, 0, 1200, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 1920, 1, 1200, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

detector_qhy600 = {
    "name": "QHY600",
    "description": "QHY600 CMOS camera",
    "ref_pixel": [4800, 3211],
    "format": [9600, 0, 0, 0, 6422, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, 9600, 1, 6422, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

x = 8288
y = 5644
detector_asi294 = {
    "name": "ASI294",
    "description": "ZWO ASI294MM Pro CMOS camera",
    "ref_pixel": [x / 2, y / 2],
    "format": [x, 0, 0, 0, y, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, x, 1, y, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}

x1 = 9576
y1 = 6388
detector_asi6200MM = {
    "name": "ASI6200MM",
    "description": "ZWO ASI6200MM Pro CMOS camera",
    "ref_pixel": [x1 / 2, y1 / 2],
    "format": [x1, 0, 0, 0, y1, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, x1, 1, y1, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}


x1 = 14208
y1 = 10656
detector_imx411 = {
    "name": "IMX411",
    "description": "IMX411 CMOS camera",
    "ref_pixel": [x1 / 2, y1 / 2],
    "format": [x1, 0, 0, 0, y1, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [0]],
    "roi": [1, x1, 1, y1, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
}


detector_sta4850 = {
    "name": "STA4850",
    "description": "STA STA4850 CCD",
    "ref_pixel": [2040, 2040],
    "format": [4080, 4, 0, 20, 4080, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 2, [0, 1, 2, 3]],
    "amp_cfg": [0, 1, 2, 3],  # fixme
    "roi": [1, 4080, 1, 4080, 1, 1],
    "ext_position": [[1, 1], [2, 1], [1, 2], [2, 2]],
    "jpg_order": [1, 2, 3, 4],
    "ext_number": [1, 2, 3, 4],
    "det_number": [1, 1, 1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
        [1, 2],
        [2, 2],
    ],
    "amp_pixel_position": [
        [1, 1],
        [4080, 1],
        [1, 4080],
        [4080, 1],
    ],
    "ext_name": [
        "im1",
        "im2",
        "im3",
        "im4",
    ],
}

detector_sta4850_2amps_side = {
    "name": "STA4850",
    "description": "STA STA4850 CCD",
    "ref_pixel": [2040, 2040],
    "format": [4080, 4, 0, 20, 4080, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 1, [0, 1]],
    "roi": [1, 4080, 1, 4080, 1, 1],
    "ext_position": [[1, 1], [2, 1]],
    "jpg_order": [1, 2],
    "ext_number": [1, 2],
    "det_number": [1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
    ],
    "amp_pixel_position": [
        [1, 1],
        [4080, 1],
    ],
    "ext_name": [
        "im1",
        "im2",
    ],
}

detector_sta4850_2amps_top = {
    "name": "STA4850",
    "description": "STA STA4850 CCD",
    "ref_pixel": [2040, 2040],
    "format": [4080, 4, 0, 20, 4080, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 1, [0, 1]],
    "roi": [1, 4080, 1, 4080, 1, 1],
    "ext_position": [[1, 1], [2, 1]],
    "jpg_order": [1, 2],
    "ext_number": [1, 2],
    "det_number": [1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
    ],
    "amp_pixel_position": [
        [1, 1],
        [4080, 1],
    ],
    "ext_name": [
        "im1",
        "im2",
    ],
    "amp_cfg": [0, 1],
}


detector_sta4850_1amp = {
    "name": "STA4850",
    "description": "STA STA4850 CCD",
    "ref_pixel": [2040, 2040],
    "format": [4080, 4, 0, 20, 4080, 0, 0, 0, 0],
    "focalplane": [1, 1, 1, 1, [1]],
    "roi": [1, 4080, 1, 4080, 1, 1],
    "ext_position": [[1, 1]],
    "jpg_order": [1],
    "ext_number": [1],
    "det_number": [1],
    "det_position": [
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
    ],
    "amp_pixel_position": [
        [1, 1],
    ],
    "ext_name": [
        "im1",
    ],
}

detector_sta0500 = {
    "name": "STA0500",
    "description": "STA STA0500 CCD",
    "ref_pixel": [2032, 2032],
    "format": [4064, 3, 0, 20, 4064, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 2, [0, 1, 2, 3]],
    "roi": [1, 4064, 1, 4064, 1, 1],
    "ext_position": [[1, 1], [2, 1], [1, 2], [2, 2]],
    "jpg_order": [1, 2, 3, 4],
    "ext_number": [1, 2, 3, 4],
    "det_number": [1, 1, 1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
        [1, 2],
        [2, 2],
    ],
    "amp_pixel_position": [
        [1, 1],
        [4064, 1],
        [1, 4064],
        [4064, 1],
    ],
    "ext_name": [
        "im1",
        "im2",
        "im3",
        "im4",
    ],
}

detector_sta4500 = {
    "name": "STA4500",
    "description": "STA STA4500 CCD",
    "ref_pixel": [3060, 3060],
    "format": [6120, 4, 0, 20, 6120, 0, 0, 0, 0],
    "focalplane": [1, 1, 2, 2, [0, 1, 2, 3]],
    "roi": [1, 6120, 1, 6120, 1, 1],
    "ext_position": [[1, 1], [2, 1], [1, 2], [2, 2]],
    "jpg_order": [1, 2, 3, 4],
    "ext_number": [1, 2, 3, 4],
    "det_number": [1, 1, 1, 1],
    "det_position": [
        [1, 1],
        [1, 1],
        [1, 1],
        [1, 1],
    ],
    "det_gap": [
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
        [0.0, 0.0],
    ],
    "amp_position": [
        [1, 1],
        [2, 1],
        [1, 2],
        [2, 2],
    ],
    "amp_pixel_position": [
        [1, 1],
        [6120, 1],
        [1, 6120],
        [6120, 1],
    ],
    "ext_name": [
        "im1",
        "im2",
        "im3",
        "im4",
    ],
}
