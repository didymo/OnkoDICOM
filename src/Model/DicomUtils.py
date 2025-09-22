

def truncate_ds_fields(ds):
    for elem in ds.iterall():
        if elem.VR == "DS":
            if isinstance(elem.value, (list, tuple)):
                # Truncate each element, ensure it's a string representing a float
                new_vals = []
                for v in elem.value:
                    try:
                        f = float(v)
                        s = f"{f:.10g}"[:16]
                        new_vals.append(s)
                    except Exception:
                        # If v is a stringified list, split and process each element
                        if isinstance(v, str) and "[" in v and "]" in v:
                            v_clean = v.strip("[] ")
                            for part in v_clean.split(","):
                                part = part.strip()
                                if part:
                                    try:
                                        f2 = float(part)
                                        s2 = f"{f2:.10g}"[:16]
                                        new_vals.append(s2)
                                    except Exception:
                                        continue
                        else:
                            continue
                elem.value = new_vals
            else:
                # Single value: ensure string, truncate, and must be convertible to float
                v = elem.value
                try:
                    f = float(v)
                    s = f"{f:.10g}"[:16]
                    elem.value = s
                except Exception:
                    # If v is a stringified list, split and use first valid float
                    if isinstance(v, str) and "[" in v and "]" in v:
                        v_clean = v.strip("[] ")
                        for part in v_clean.split(","):
                            part = part.strip()
                            if part:
                                try:
                                    f2 = float(part)
                                    s2 = f"{f2:.10g}"[:16]
                                    elem.value = s2
                                    break
                                except Exception:
                                    continue
                    else:
                        continue