import datetime
import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import duplicateChecker as dc  # noqa: E402
import photoSort as ps  # noqa: E402


def make_img(path, date=None, color=(255, 0, 0), size=(8, 8)):
    img = Image.new("RGB", size, color)
    kwargs = {}
    if date:
        exif = Image.Exif()
        exif.get_ifd(ps.EXIF_IFD_POINTER)[ps.TAG_DATETIME_ORIGINAL] = date
        kwargs["exif"] = exif
    img.save(path, "PNG" if path.suffix == ".png" else "JPEG", **kwargs)


def test_exif_date_read(tmp_path):
    p = tmp_path / "a.jpg"
    make_img(p, "2024:03:05 10:11:12")
    assert ps.get_date_time_original(p) == "2024:03:05 10:11:12"


def test_week_dates_use_iso_year():
    d = datetime.datetime(2025, 12, 30)  # ISO week 1 of 2026
    y, w, _ = d.isocalendar()
    assert (y, w) == (2026, 1)
    assert ps.get_week_dates(y, w) == ("29.12", "04.01")


def test_rename_never_overwrites_and_is_idempotent(tmp_path):
    a, b = tmp_path / "a.jpg", tmp_path / "b.jpg"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    ra = ps.rename_file(a, "2024:03:05 10:11:12")
    rb = ps.rename_file(b, "2024:03:05 10:11:12")
    assert ra.name == "2024_03_05_101112.jpg"
    assert rb.name == "2024_03_05_101112_(1).jpg"
    assert ra.read_bytes() == b"a" and rb.read_bytes() == b"b"
    assert ps.rename_file(ra, "2024:03:05 10:11:12") == ra


def test_sort_collision_keeps_both(tmp_path):
    src, out = tmp_path / "src", tmp_path / "out"
    (src / "x").mkdir(parents=True)
    ts = datetime.datetime(2024, 3, 5, 10).timestamp()
    for name, data in (("p.jpg", b"1"), ("x/p.jpg", b"2")):
        (src / name).write_bytes(data)
        os.utime(src / name, (ts, ts))
    ps.process_media(str(src), str(out), should_sort=True, assume_yes=True)
    moved = sorted(out.rglob("*.jpg"))
    assert len(moved) == 2 and {m.read_bytes() for m in moved} == {b"1", b"2"}


def test_output_inside_source_not_reprocessed(tmp_path):
    src = tmp_path / "src"
    out = src / "sorted"
    src.mkdir()
    (src / "p.jpg").write_bytes(b"1")
    ps.process_media(str(src), str(out), should_sort=True, assume_yes=True)
    ps.process_media(str(src), str(out), should_sort=True, assume_yes=True)
    assert len(list(out.rglob("*.jpg"))) == 1


def test_dry_run_changes_nothing(tmp_path):
    (tmp_path / "p.jpg").write_bytes(b"1")
    ps.process_media(str(tmp_path), str(tmp_path / "o"), True, True, assume_yes=True, dry_run=True)
    assert [p.name for p in tmp_path.iterdir()] == ["p.jpg"]


def test_duplicates_moved_without_overwrite(tmp_path):
    (tmp_path / "s").mkdir()
    make_img(tmp_path / "a.png", color=(1, 2, 3))
    make_img(tmp_path / "s" / "a.png", color=(1, 2, 3))
    make_img(tmp_path / "other.png", color=(9, 9, 9))
    dup = tmp_path / "dups"
    dup.mkdir()
    (dup / "a.png").write_bytes(b"existing")
    dc.find_and_remove_duplicates(tmp_path, dup)
    assert (dup / "a.png").read_bytes() == b"existing"
    assert (dup / "a_(1).png").exists()
    assert len(list(tmp_path.rglob("a.png"))) == 2  # one kept + the pre-existing one in dups


def test_hash_distinguishes_size_and_skips_animated(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    make_img(a, size=(4, 16))
    make_img(b, size=(16, 4))
    assert dc.get_image_hash(a) != dc.get_image_hash(b)
    g = tmp_path / "g.png"
    frames = [Image.new("RGB", (4, 4), c) for c in ((0, 0, 0), (255, 255, 255))]
    frames[0].save(g, save_all=True, append_images=frames[1:])
    assert dc.get_image_hash(g) is None
