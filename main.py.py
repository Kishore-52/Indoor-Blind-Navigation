import cv2
import os
import sys
import time
import subprocess
from statistics import median

import RPi.GPIO as GPIO
from edge_impulse_linux.image import ImageImpulseRunner

try:
    from mpu6050 import mpu6050
    IMU_AVAILABLE = True
except Exception:
    IMU_AVAILABLE = False


# ============================================================
# VISIONGUIDE AI - VIVA STABLE VERSION
# ============================================================

MODEL_PATH = "/home/hackathon/visionGuideAI/model.eim"
AUDIO_FOLDER = "/home/hackathon/visionGuideAI/audio"

# False = touch sensor controls system ON/OFF.
# Emergency fallback: change to True if you need the system always ON.
DEMO_ALWAYS_ON = False

TOUCH_PIN = 5

# TTP223-style touch modules normally output HIGH while touched.
# Change to False only if your module outputs LOW while touched.
TOUCH_ACTIVE_HIGH = True

# Touch filtering prevents one touch from toggling repeatedly.
TOUCH_DEBOUNCE_SECONDS = 0.08
TOUCH_LOCKOUT_SECONDS = 1.00

ULTRASONIC_SENSORS = {
    "front": {"trig": 23, "echo": 24},
    "left": {"trig": 17, "echo": 27},
    "right": {"trig": 22, "echo": 10},
    "back": {"trig": 9, "echo": 11},
}

STOP_DISTANCE = 0.70
WARNING_DISTANCE = 1.50
BACK_WARNING_DISTANCE = 0.80
SAFE_SIDE_MIN_DISTANCE = 0.90

# Per-class audio cooldown. Staircase is intentionally much longer
# because it was repeatedly announced during live testing.
LABEL_AUDIO_COOLDOWN = {
    "chair": 10.0,
    "door": 10.0,
    "person": 10.0,
    "table": 10.0,
}

# Exact thresholds requested:
# staircase = 1.00; all remaining objects = 0.90
CONFIDENCE_THRESHOLD = {
    "chair": 0.90,
    "door": 0.90,
    "person": 0.90,
    "table": 0.90,
}

# Exact stable-frame requirements requested:
# staircase = 10 frames; all remaining objects = 7 frames
REQUIRED_FRAMES = {
    "chair": 7,
    "door": 7,
    "person": 7,
    "staircase": 10,
    "table": 7,
}

# Top prediction must also be clearly above the second prediction.
# This reduces noisy classifications.
MIN_CONFIDENCE_MARGIN = {
    "chair": 0.10,
    "door": 0.10,
    "person": 0.10,
    "staircase": 0.25,
    "table": 0.10,
}

# Explicit object-to-audio mapping. There is deliberately no generic
# "obstacle detected" fallback for classified objects.
OBJECT_AUDIO_MAP = {
    "chair": "chair.mp3",
    "door": "door.mp3",
    "person": "person.mp3",
    "staircase": "staircase.mp3",
    "table": "table.mp3",
}

SYSTEM_AUDIO_MAP = {
    "system_on": "system_on.mp3",
    "system_off": "system_off.mp3",
    "stop": "stop.mp3",
    "move_left": "move_left.mp3",
    "move_right": "move_right.mp3",
    "obstacle_behind": "obstacle_behind.mp3",
    "fall_detected": "fall_detected.mp3",
    "sensor_error": "sensor_error.mp3",
}

LABEL_ALIASES = {
    "people": "person",
    "human": "person",
    "stairs": "staircase",
    "stair": "staircase",
    "dining table": "table",
}

# Ultrasonic smoothing. Median of 3 samples reduces random distance spikes.
DISTANCE_SAMPLES = 3


# ============================================================
# GLOBAL STATE
# ============================================================

system_active = DEMO_ALWAYS_ON
last_touch_time = 0.0

# Debounced touch state.
touch_last_raw_active = False
touch_stable_active = False
touch_last_raw_change = 0.0
touch_armed = True

stable_label = None
stable_count = 0

# Audio announcement state.
last_announced_label = None
last_announcement_by_label = {}

imu_sensor = None
fall_count = 0


# ============================================================
# AUDIO
# ============================================================

def run_command(command):
    """Run audio commands synchronously so clips do not overlap."""
    try:
        subprocess.run(command, check=False)
    except FileNotFoundError:
        print("Command not installed:", command[0])
    except Exception as error:
        print("Audio command error:", error)


def play_file(filename, description):
    audio_path = os.path.join(AUDIO_FOLDER, filename)

    if not os.path.isfile(audio_path):
        print("Missing audio file:", audio_path)
        return False

    print(f"Playing {description}: {audio_path}")
    run_command(["mpg123", "-q", audio_path])
    return True


def play_object_audio(label):
    """
    Plays only the file belonging to the predicted object.
    Example: person -> person.mp3. No generic fallback is used.
    """
    filename = OBJECT_AUDIO_MAP.get(label)

    if filename is None:
        print("No object audio mapping for:", label)
        return False

    return play_file(filename, f"object '{label}'")


def play_system_audio(audio_key):
    filename = SYSTEM_AUDIO_MAP.get(audio_key)

    if filename is None:
        print("No system audio mapping for:", audio_key)
        return False

    return play_file(filename, f"system alert '{audio_key}'")


def speak_text(text):
    print("Voice:", text)
    run_command(["espeak-ng", text])


def speak_distance(distance, direction="ahead"):
    if distance is None:
        return

    if distance < 0.40:
        text = f"very close {direction}"
    elif distance < 1.00:
        centimeters = int(round(distance * 100))
        text = f"{centimeters} centimeters {direction}"
    else:
        rounded_distance = round(distance, 1)
        unit = "meter" if rounded_distance == 1.0 else "meters"
        text = f"{rounded_distance:g} {unit} {direction}"

    speak_text(text)


def speak_object_with_distance(label, distance):
    """
    Speaks one continuous real-time guidance sentence using:
    - object label from model.eim
    - distance from the front ultrasonic sensor

    Examples:
        Person ahead, 1.2 meters.
        Chair ahead, 75 centimeters.
        Staircase ahead, very close.
    """
    object_name = str(label).strip().replace("_", " ").title()

    if distance is None:
        speak_text(f"{object_name} ahead")
        return

    if distance < 0.40:
        text = f"{object_name} ahead, very close"
    elif distance < 1.00:
        centimeters = int(round(distance * 100))
        text = f"{object_name} ahead, {centimeters} centimeters"
    else:
        rounded_distance = round(distance, 1)
        unit = "meter" if rounded_distance == 1.0 else "meters"
        text = f"{object_name} ahead, {rounded_distance:g} {unit}"

    print(
        f"Combined guidance: label={label}, "
        f"front_distance={distance} m, voice='{text}'"
    )
    speak_text(text)


def speak_side_distance(distance, side):
    if distance is None:
        return

    if distance < 1.00:
        centimeters = int(round(distance * 100))
        text = f"{side} side is clear for {centimeters} centimeters"
    else:
        rounded_distance = round(distance, 1)
        unit = "meter" if rounded_distance == 1.0 else "meters"
        text = f"{side} side is clear for {rounded_distance:g} {unit}"

    speak_text(text)


def validate_audio_files():
    print("\nChecking audio mappings...")
    all_files = {**OBJECT_AUDIO_MAP, **SYSTEM_AUDIO_MAP}
    missing = []

    for key, filename in all_files.items():
        path = os.path.join(AUDIO_FOLDER, filename)
        status = "OK" if os.path.isfile(path) else "MISSING"
        print(f"{key:18s} -> {filename:24s} [{status}]")
        if status == "MISSING":
            missing.append(path)

    if missing:
        print("\nMissing audio files:")
        for path in missing:
            print(" -", path)
    else:
        print("All required audio files are present.")


def test_object_audio_files():
    """Run with: python3 main_viva_fixed.py --test-audio"""
    validate_audio_files()
    print("\nTesting object audio in mapping order...")

    for label in ("person", "chair", "door", "table", "staircase"):
        print("Expected object:", label)
        play_object_audio(label)
        time.sleep(0.3)


# ============================================================
# GPIO SETUP
# ============================================================

def touch_is_active():
    """Return True only while the touch module is actively touched."""
    raw_value = GPIO.input(TOUCH_PIN)

    if TOUCH_ACTIVE_HIGH:
        return raw_value == GPIO.HIGH

    return raw_value == GPIO.LOW


def setup_gpio():
    global touch_last_raw_active
    global touch_stable_active
    global touch_last_raw_change
    global touch_armed

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    # PUD_DOWN is suitable for an active-HIGH touch module.
    # For an active-LOW module, use PUD_UP.
    pull_mode = GPIO.PUD_DOWN if TOUCH_ACTIVE_HIGH else GPIO.PUD_UP
    GPIO.setup(TOUCH_PIN, GPIO.IN, pull_up_down=pull_mode)

    for sensor in ULTRASONIC_SENSORS.values():
        GPIO.setup(sensor["trig"], GPIO.OUT)
        GPIO.setup(sensor["echo"], GPIO.IN)
        GPIO.output(sensor["trig"], False)

    time.sleep(0.5)

    # Prevent an already-HIGH sensor during boot from toggling automatically.
    initial_active = touch_is_active()
    touch_last_raw_active = initial_active
    touch_stable_active = initial_active
    touch_last_raw_change = time.monotonic()
    touch_armed = not initial_active

    print(
        "Touch sensor initialized:",
        "ACTIVE" if initial_active else "released",
        "| GPIO",
        TOUCH_PIN,
    )

    time.sleep(0.5)


# ============================================================
# ULTRASONIC SENSOR
# ============================================================

def get_distance_once(sensor_name):
    trig = ULTRASONIC_SENSORS[sensor_name]["trig"]
    echo = ULTRASONIC_SENSORS[sensor_name]["echo"]

    try:
        GPIO.output(trig, False)
        time.sleep(0.0002)

        GPIO.output(trig, True)
        time.sleep(0.00001)
        GPIO.output(trig, False)

        wait_start = time.monotonic()
        pulse_start = wait_start

        while GPIO.input(echo) == 0:
            pulse_start = time.monotonic()
            if pulse_start - wait_start > 0.03:
                return None

        wait_start = time.monotonic()
        pulse_end = wait_start

        while GPIO.input(echo) == 1:
            pulse_end = time.monotonic()
            if pulse_end - wait_start > 0.03:
                return None

        pulse_duration = pulse_end - pulse_start
        distance_m = (pulse_duration * 343.0) / 2.0

        if not 0.02 <= distance_m <= 4.00:
            return None

        return distance_m

    except Exception as error:
        print(f"{sensor_name} ultrasonic error:", error)
        return None


def get_distance(sensor_name):
    valid_samples = []

    for _ in range(DISTANCE_SAMPLES):
        value = get_distance_once(sensor_name)
        if value is not None:
            valid_samples.append(value)
        time.sleep(0.01)

    if not valid_samples:
        return None

    return round(median(valid_samples), 2)


def read_all_distances():
    distances = {
        "front": get_distance("front"),
        "left": get_distance("left"),
        "right": get_distance("right"),
        "back": get_distance("back"),
    }
    print("Ultrasonic distances:", distances)
    return distances


# ============================================================
# TOUCH SENSOR
# ============================================================

def reset_announcement_state():
    """Allow fresh announcements after the system is turned back ON."""
    global last_announced_label
    global last_announcement_by_label

    last_announced_label = None
    last_announcement_by_label = {}


def check_touch_toggle():
    """
    Debounced rising-edge touch control.

    One physical touch toggles the system exactly once.
    The sensor must be released before another touch is accepted.
    """
    global system_active
    global last_touch_time
    global touch_last_raw_active
    global touch_stable_active
    global touch_last_raw_change
    global touch_armed

    if DEMO_ALWAYS_ON:
        return

    now = time.monotonic()
    raw_active = touch_is_active()

    # Start debounce timing whenever the raw input changes.
    if raw_active != touch_last_raw_active:
        touch_last_raw_active = raw_active
        touch_last_raw_change = now
        return

    # Ignore the input until it remains unchanged long enough.
    if now - touch_last_raw_change < TOUCH_DEBOUNCE_SECONDS:
        return

    # Stable state changed from released to touched.
    if raw_active and not touch_stable_active:
        touch_stable_active = True

        if touch_armed and now - last_touch_time >= TOUCH_LOCKOUT_SECONDS:
            system_active = not system_active
            last_touch_time = now
            touch_armed = False

            reset_stability()
            reset_announcement_state()

            if system_active:
                print("TOUCH EVENT: System ON")
                play_system_audio("system_on")
            else:
                print("TOUCH EVENT: System OFF")
                play_system_audio("system_off")

        return

    # Stable state changed from touched to released.
    if not raw_active and touch_stable_active:
        touch_stable_active = False
        touch_armed = True
        print("Touch sensor released and re-armed")


# ============================================================
# IMU
# ============================================================

def setup_imu():
    global imu_sensor

    if not IMU_AVAILABLE:
        print("IMU library not available. Skipping IMU.")
        return

    try:
        imu_sensor = mpu6050(0x68)
        print("IMU initialized.")
    except Exception as error:
        imu_sensor = None
        print("IMU failed:", error)


def check_fall_detection():
    """Requires three consecutive abnormal samples to reduce false alarms."""
    global fall_count

    if imu_sensor is None:
        return False

    try:
        data = imu_sensor.get_accel_data()
        x, y, z = data["x"], data["y"], data["z"]
        magnitude = (x ** 2 + y ** 2 + z ** 2) ** 0.5

        if magnitude > 22.0 or magnitude < 2.5:
            fall_count += 1
        else:
            fall_count = 0

        if fall_count >= 3:
            fall_count = 0
            return True

    except Exception as error:
        print("IMU read error:", error)

    return False


# ============================================================
# EDGE IMPULSE PREDICTION
# ============================================================

def normalize_label(label):
    clean_label = str(label).strip().lower().replace("_", " ")
    return LABEL_ALIASES.get(clean_label, clean_label)


def get_prediction_from_frame(runner, frame):
    try:
        features, _ = runner.get_features_from_image(frame)
        result = runner.classify(features)

        raw_predictions = result["result"]["classification"]
        predictions = {
            normalize_label(label): float(score)
            for label, score in raw_predictions.items()
        }

        ranked = sorted(
            predictions.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        if not ranked:
            return None, 0.0, None, 0.0

        best_label, best_confidence = ranked[0]

        if len(ranked) > 1:
            second_label, second_confidence = ranked[1]
        else:
            second_label, second_confidence = None, 0.0

        margin = best_confidence - second_confidence

        print(
            f"Top: {best_label} {best_confidence:.4f} | "
            f"Second: {second_label} {second_confidence:.4f} | "
            f"Margin: {margin:.4f}"
        )

        return best_label, best_confidence, second_label, second_confidence

    except Exception as error:
        print("Prediction error:", error)
        return None, 0.0, None, 0.0


def reset_stability():
    global stable_label, stable_count
    stable_label = None
    stable_count = 0


def update_stable_prediction(label, confidence, second_confidence):
    """
    Applies class threshold, confidence margin, and consecutive-frame rule.
    Returns a stable label only when all three checks pass.
    """
    global stable_label, stable_count

    if label not in CONFIDENCE_THRESHOLD:
        print("Unknown model label ignored:", label)
        reset_stability()
        return None

    threshold = CONFIDENCE_THRESHOLD[label]
    required_frames = REQUIRED_FRAMES[label]
    margin_required = MIN_CONFIDENCE_MARGIN[label]
    margin = confidence - second_confidence

    # The requested staircase threshold is exactly 1.00.
    if confidence < threshold:
        print(
            f"Rejected {label}: confidence {confidence:.4f} "
            f"< required {threshold:.2f}"
        )
        reset_stability()
        return None

    if margin < margin_required:
        print(
            f"Rejected {label}: prediction margin {margin:.4f} "
            f"< required {margin_required:.2f}"
        )
        reset_stability()
        return None

    if label == stable_label:
        stable_count += 1
    else:
        stable_label = label
        stable_count = 1

    print(
        f"Stability: {label} {stable_count}/{required_frames} "
        f"at confidence {confidence:.4f}"
    )

    if stable_count >= required_frames:
        return label

    return None


# ============================================================
# NAVIGATION DECISION
# ============================================================

def choose_safe_direction(distances):
    left = distances.get("left")
    right = distances.get("right")

    if left is None and right is None:
        return None

    if left is None:
        return "move_right" if right >= SAFE_SIDE_MIN_DISTANCE else None

    if right is None:
        return "move_left" if left >= SAFE_SIDE_MIN_DISTANCE else None

    best_side_distance = max(left, right)
    if best_side_distance < SAFE_SIDE_MIN_DISTANCE:
        return None

    return "move_left" if left > right else "move_right"


def should_announce(label):
    """
    Prevent repeated audio.

    A new class can be spoken immediately. The same class can only be
    repeated after its own cooldown. Staircase uses a 60-second cooldown.
    """
    global last_announced_label
    global last_announcement_by_label

    now = time.monotonic()
    cooldown = LABEL_AUDIO_COOLDOWN.get(label, 10.0)
    last_time = last_announcement_by_label.get(label)

    # First announcement of this class.
    if last_time is None:
        last_announced_label = label
        last_announcement_by_label[label] = now
        return True

    elapsed = now - last_time

    # A newly changed class is announced, provided that class itself is
    # not still inside its cooldown.
    if label != last_announced_label and elapsed >= 1.0:
        last_announced_label = label
        last_announcement_by_label[label] = now
        return True

    # Repeating the same class requires the full class-specific cooldown.
    if elapsed >= cooldown:
        last_announced_label = label
        last_announcement_by_label[label] = now
        return True

    remaining = cooldown - elapsed
    print(f"{label} audio suppressed: {remaining:.1f}s cooldown remaining")
    return False


def navigation_decision(label, confidence, distances):
    front = distances.get("front")
    left = distances.get("left")
    right = distances.get("right")
    back = distances.get("back")

    if not should_announce(label):
        return

    print(
        f"CONFIRMED OBJECT: {label.upper()} | "
        f"confidence={confidence:.4f} | distances={distances}"
    )

    # Priority 1: a confirmed object in front within the warning zone.
    if front is not None and front <= WARNING_DISTANCE:
        # Speak the correct model label and live ultrasonic distance
        # as one continuous sentence.
        # Example: "Person ahead, 1.2 meters."
        speak_object_with_distance(label, front)

        if front <= STOP_DISTANCE:
            play_system_audio("stop")
            return

        direction = choose_safe_direction(distances)

        if direction == "move_left":
            play_system_audio("move_left")
            speak_side_distance(left, "left")
        elif direction == "move_right":
            play_system_audio("move_right")
            speak_side_distance(right, "right")
        else:
            print("No side is safely clear; no turn instruction played.")

        return

    # If the front sensor is unavailable, still speak the exact model label.
    # This intentionally avoids any generic "obstacle detected" recording.
    if front is None:
        print("Front ultrasonic unavailable. Speaking camera label only.")
        speak_object_with_distance(label, None)
        return

    # If the confirmed front object is outside the warning distance,
    # do not produce unnecessary audio. A close rear obstacle still has priority.
    if back is not None and back <= BACK_WARNING_DISTANCE:
        play_system_audio("obstacle_behind")
        speak_distance(back, "behind")
        return

    print(f"Confirmed {label}, but it is outside warning distance: {front} m")


def test_touch_sensor():
    """
    Run with:
        python3 main_viva_touch_audio_fixed.py --test-touch

    Touch and release the sensor several times. The terminal should print
    one ON/OFF event per touch.
    """
    global system_active

    setup_gpio()
    system_active = False

    print("\nTouch test started.")
    print("Touch once for ON, release, then touch again for OFF.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            check_touch_toggle()
            print(
                f"raw={GPIO.input(TOUCH_PIN)} "
                f"active={touch_is_active()} "
                f"system_active={system_active}",
                end="\r",
                flush=True,
            )
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\nTouch test stopped.")
    finally:
        GPIO.cleanup()


# ============================================================
# MAIN
# ============================================================

def main():
    setup_gpio()
    setup_imu()
    validate_audio_files()

    runner = None
    cap = None

    try:
        print("Loading Edge Impulse model...")
        runner = ImageImpulseRunner(MODEL_PATH)
        model_info = runner.init()

        model_labels = [normalize_label(x) for x in model_info["model_parameters"]["labels"]]
        print("Model loaded.")
        print("Model labels:", model_labels)

        required_labels = set(CONFIDENCE_THRESHOLD)
        missing_labels = required_labels.difference(model_labels)
        if missing_labels:
            print("WARNING: These required labels are not in model.eim:", sorted(missing_labels))

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            print("Camera not found.")
            play_system_audio("sensor_error")
            return

        print("System ready.")

        if DEMO_ALWAYS_ON:
            print("VIVA DEMO MODE: system is always ON.")
            play_system_audio("system_on")
        else:
            print("Touch sensor controls ON/OFF.")

        while True:
            check_touch_toggle()

            if not system_active:
                time.sleep(0.1)
                continue

            if check_fall_detection():
                print("Fall detected")
                play_system_audio("fall_detected")
                reset_stability()
                time.sleep(1)
                continue

            ret, frame = cap.read()

            if not ret:
                print("Camera frame error")
                play_system_audio("sensor_error")
                time.sleep(0.5)
                continue

            label, confidence, second_label, second_confidence = get_prediction_from_frame(
                runner, frame
            )

            confirmed_label = None
            if label is not None:
                confirmed_label = update_stable_prediction(
                    label,
                    confidence,
                    second_confidence,
                )

            # Read ultrasonic sensors only after a class becomes stable.
            # This keeps camera inference responsive while counting frames.
            if confirmed_label is not None:
                distances = read_all_distances()
                navigation_decision(confirmed_label, confidence, distances)
                reset_stability()

            display_label = label if label is not None else "uncertain"
            threshold = CONFIDENCE_THRESHOLD.get(label, 0.0)
            required = REQUIRED_FRAMES.get(label, 0)
            progress = stable_count if label == stable_label else 0

            cv2.putText(
                frame,
                f"{display_label}: {confidence:.3f}",
                (25, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.85,
                (0, 255, 0),
                2,
            )
            cv2.putText(
                frame,
                f"Threshold: {threshold:.2f}  Stable: {progress}/{required}",
                (25, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
            )

            cv2.imshow("VisionGuide AI - Viva Stable Mode", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord("q"):
                break

    except KeyboardInterrupt:
        print("Stopped by user.")

    except Exception as error:
        print("Main error:", error)
        play_system_audio("sensor_error")

    finally:
        if cap is not None:
            cap.release()

        if runner is not None:
            runner.stop()

        GPIO.cleanup()
        cv2.destroyAllWindows()
        print("System closed.")


if __name__ == "__main__":
    if "--test-audio" in sys.argv:
        test_object_audio_files()
        sys.exit(0)

    if "--test-guidance" in sys.argv:
        print("Testing exact object and distance guidance...")
        speak_object_with_distance("person", 1.2)
        speak_object_with_distance("chair", 0.75)
        speak_object_with_distance("door", 1.0)
        speak_object_with_distance("table", 1.4)
        speak_object_with_distance("staircase", 0.35)
        sys.exit(0)

    if "--test-touch" in sys.argv:
        test_touch_sensor()
        sys.exit(0)

    main()
