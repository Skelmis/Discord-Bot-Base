import re

time_regex = re.compile(r"(( ?(\d{1,5})(h|s|m|d))+)")
time_dict = {"h": 3600, "s": 1, "m": 60, "d": 86400}


async def time_convertor(argument):
    raise RuntimeWarning("Lol dont")
    args = argument.lower()
    matches = re.findall(time_regex, args)
    if not matches:
        return 0

    matches = matches[0][0].split(" ")
    matches = [filter(None, re.split(r"(\d+)", s)) for s in matches]
    time = 0
    for match in matches:
        key, value = match
        try:
            time += time_dict[value] * float(key)
        except KeyError:
            raise commands.BadArgument(
                f"{value} is an invalid time key! h|m|s|d are valid arguments"
            )
        except ValueError:
            raise commands.BadArgument(f"{key} is not a number!")
    return time
