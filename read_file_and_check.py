import numpy as np
import pandas as pd
import cv2

def create_frame(events_df, gaze_x, gaze_y, h=720, w=1280):
    # Convert DataFrame to structured numpy array for events
    events = np.array(list(zip(events_df['x'], events_df['y'], 
                              events_df['p'], events_df['t'])), 
                     dtype=[('x', '<u2'), ('y', '<u2'), 
                           ('p', '<i2'), ('t', '<i8')])

    # Create base image
    img = np.ones((h, w, 3), dtype=np.uint8) * 127

    # Plot events
    if events.size:
        assert events['x'].max() < w, "out of bound events: x = {}, w = {}".format(events['x'].max(), w)
        assert events['y'].max() < h, "out of bound events: y = {}, h = {}".format(events['y'].max(), h)
        img[events['y'], events['x'], :] = 255 * events['p'][:, None]
    
    # Draw gaze point
    gaze_x = int(gaze_x * w / 1920)  # Scale from 1920 to frame width
    gaze_y = int(gaze_y * h / 1080)  # Scale from 1080 to frame height
    cv2.circle(img, (gaze_x, gaze_y), 5, (0, 0, 255), -1)  # Draw red circle

    return img

def filter_events_by_timerange(events_df, start_time, end_time):
    mask = (events_df['t'] >= start_time) & (events_df['t'] <= end_time)
    return events_df[mask]

# Load the CSVs
label_csv = pd.read_csv("smooth_log.csv")
events_csv = pd.read_csv("recording_250218_233826.csv")
events_csv.columns = ['x', 'y', 'p', 't']

print("Events data head:")
print(events_csv.head())
print("\nLabel data head:")
print(label_csv.head())

# Create window
cv2.namedWindow('Visualization', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Visualization', 1280, 720)

for idx, item in label_csv.iterrows():
    # Get timestamps
    end_timestamp = item['Timestamp_ms']
    start_timestamp = item['Timestamp_ms'] - 33000
    
    print(f"\nProcessing frame {idx}")
    print(f"Time window: {start_timestamp} to {end_timestamp}")
    
    # Filter events
    filtered_df = filter_events_by_timerange(events_csv, start_timestamp, end_timestamp)
    print(f"Number of events in window: {filtered_df.shape[0]}")
    
    # Create and display frame
    img = create_frame(filtered_df, item['X'], item['Y'])
    cv2.imshow('Visualization', img)
    
    # Save frame (optional)
    # cv2.imwrite(f'frame_{idx:04d}.png', img)
    
    # Wait for key press
    key = cv2.waitKey(100)  # Wait 100ms between frames
    if key & 0xFF == ord('q'):
        break
    elif key & 0xFF == ord(' '):  # Space to pause
        cv2.waitKey(0)

# Clean up
cv2.destroyAllWindows()