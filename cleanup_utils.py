import sqlite3
from datetime import datetime, date


def cleanup_expired_rides():
    """
    Deletes rides that have already occurred (past their date).
    This function is called via cron job and on key page loads.

    Returns a dictionary with the results of the cleanup operation.
    """
    try:
        # Connect to the database
        conn = sqlite3.connect('rides.db')
        c = conn.cursor()

        # Get today's date
        today = date.today().strftime('%Y-%m-%d')

        # Find expired rides (rides with dates before today)
        c.execute("SELECT id FROM rides WHERE date < ?", (today,))
        expired_ride_ids = [row[0] for row in c.fetchall()]

        # Count of expired rides
        expired_count = len(expired_ride_ids)

        if expired_count > 0:
            # Delete applications for expired rides
            placeholders = ','.join(['?' for _ in expired_ride_ids])
            c.execute(f"DELETE FROM applications WHERE ride_id IN ({placeholders})", expired_ride_ids)

            # Delete the expired rides
            c.execute(f"DELETE FROM rides WHERE id IN ({placeholders})", expired_ride_ids)

            # Commit the changes
            conn.commit()

            print(f"Cleanup: Deleted {expired_count} expired rides")
        else:
            print("Cleanup: No expired rides to delete")

        conn.close()

        return {
            "success": True,
            "deleted_rides_count": expired_count,
            "timestamp": datetime.now().isoformat(),
            "message": f"Successfully deleted {expired_count} expired rides"
        }

    except Exception as e:
        error_message = f"Cleanup error: {str(e)}"
        print(error_message)
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }
