
def anet_conv(millis: int, framerate: int):
    frames = (millis * framerate/1000) % framerate
    a_fr = int(frames)
    seconds = (millis / 1000) % 60
    a_sec = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    a_min = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24
    a_hour = int(hours)

    header = bytearray()
    list1 = []
    # ID
    header.extend(bytearray('Art-Net', 'utf8'))
    header.append(0x0)
    # OpCodeLo
    header.append(0x0)
    # OpCodeHi
    header.append(0x97)
    # ProtVerHi
    header.append(0x0)
    # ProtVerLo
    header.append(0xE)
    # Filler1
    header.append(0x0)
    # Filler2
    header.append(0x0)
    # Frames
    header.append(a_fr)
    # header.extend(bytearray(a_fr, 'utf8'))
    # Seconds
    header.append(a_sec)
    # header.extend(bytearray(a_sec, 'utf8'))
    # Minutes
    header.append(a_min)
    # header.extend(bytearray(a_min, 'utf8'))
    # Hours
    header.append(a_hour)
    # header.extend(bytearray(a_hour, 'utf8'))
    # Type
    header.append(0x3)
    full = header
    return full


def millis_to_tc(millis: int, framerate: int):
    frames = (millis / 1000 * framerate) % framerate
    #if millis < 1000:
    #    frames = millis*framerate
    frames = int(frames)
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    hours = (millis / (1000 * 60 * 60)) % 24
    hours = int(hours)
    if int(hours) <= 9:
        hours = '0'+str(hours)
    if int(minutes) <= 9:
        minutes = '0'+str(minutes)
    if int(seconds) <= 9:
        seconds = '0'+str(seconds)
    if int(frames) <= 9:
        frames = '0'+str(frames)
    tc_string = str(hours) + ":" + str(minutes) + ":" + str(seconds) + ":" + str(frames)
    return tc_string
