import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from tkcalendar import Calendar
import sqlite3
from datetime import datetime


class RoomBookingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Room Booking App")

        self.conn = sqlite3.connect('room_booking.db')
        self.create_table()

        # Start with the login UI
        self.username = None  # Initially, no user is logged in
        self.build_login_ui()

    def build_login_ui(self):
        # Login frame
        self.login_frame = tk.Frame(self.master)
        self.login_frame.pack()

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        login_button = tk.Button(
            self.login_frame, text="Login", command=self.attempt_login)
        login_button.grid(row=2, column=0, columnspan=2)

        # Show login frame and bring it to the front
        self.master.wait_visibility()  # Wait until the master is visible
        self.login_frame.lift()  # Bring the login frame to the top


    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY,
                room_id INTEGER,
                date_time TEXT,
                username TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms (id),
                FOREIGN KEY (username) REFERENCES users (username)
            )''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT
            )''')
        # Insert a default user for simplicity, adjust as needed for your application
        cursor.execute(
            "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", ("admin", "admin"))
        self.conn.commit()



    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE username=?", (username,))
        result = cursor.fetchone()
        if result and result[0] == password:
            messagebox.showinfo("Login", "Login Successful")
            self.username = username  # Set the username attribute
            self.master.deiconify()  # Show the main window
            self.initialize_ui()  # Initialize the rest of the UI
            self.login_frame.destroy()  # Remove the login frame
        else:
            messagebox.showerror("Login", "Login Failed")
            self.username_entry.delete(0, tk.END)  # Clear the username entry
            self.password_entry.delete(0, tk.END)  # Clear the password entry

    def initialize_ui(self):
        # Create the menu
        self.menu = tk.Menu(self.master)
        self.master.config(menu=self.menu)

        # Create a file menu
        self.file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=self.file_menu)

        # Add items to the file menu
        self.file_menu.add_command(
            label="Create Meeting", command=self.create_meeting)
        self.file_menu.add_command(
            label="Create Room", command=self.create_room)
        self.file_menu.add_command(
            label="Display Rooms", command=self.display_rooms)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quit", command=self.quit_app)

        # Room selection Combobox
        self.room_selection = ttk.Combobox(self.master)
        self.room_selection.pack()

        # Calendar
        self.calendar_frame = tk.Frame(self.master)
        self.calendar_frame.pack()
        self.calendar = Calendar(
            self.calendar_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendar.pack()
        self.calendar.bind("<<CalendarSelected>>", self.load_meetings)

        # Listbox to display meetings
        self.meetings_listbox = tk.Listbox(self.master)
        self.meetings_listbox.pack(fill="both", expand=True)

        # Populate the rooms combobox
        self.load_rooms()


    def load_rooms(self):

        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM rooms")
        rooms = cursor.fetchall()
        room_names = [room[0] for room in rooms]
        self.room_selection['values'] = room_names
        if room_names:
            self.room_selection.set(room_names[0])

    def create_room(self):
        room_name = simpledialog.askstring("Create Room", "Enter Room Name:")
        if room_name:
            cursor = self.conn.cursor()
            try:
                cursor.execute(
                    "INSERT INTO rooms (name) VALUES (?)", (room_name,))
                self.conn.commit()
                messagebox.showinfo("Success", "Room created successfully!")
                self.load_rooms()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Room already exists!")

    def create_meeting(self):
        room_name = self.room_selection.get()
        if room_name:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM rooms WHERE name=?", (room_name,))
            room = cursor.fetchone()
            if room:
                selected_date = self.calendar.get_date()
                top = tk.Toplevel()
                top.title("Select Time")

                times = ["09:00", "10:00", "11:00", "12:00",
                        "13:00", "14:00", "15:00", "16:00"]
                time_var = tk.StringVar()
                time_var.set(times[0])
                time_option = tk.OptionMenu(top, time_var, *times)
                time_option.pack()

                def save_meeting():
                    selected_time = time_var.get()
                    date_time = f"{selected_date} {selected_time}"
                    try:
                        cursor.execute(
                            "INSERT INTO meetings (room_id, date_time, username) VALUES (?, ?, ?)",
                            (room[0], date_time, self.username)
                        )
                        self.conn.commit()
                        messagebox.showinfo(
                            "Success", "Meeting created successfully!")
                        top.destroy()
                        self.load_meetings()
                    except sqlite3.Error as e:
                        messagebox.showerror("Error", f"An error occurred: {e}")

                save_button = tk.Button(top, text="Save", command=save_meeting)
                save_button.pack()

                cancel_button = tk.Button(top, text="Cancel", command=top.destroy)
                cancel_button.pack()

            else:
                messagebox.showerror("Error", "Room does not exist!")
        else:
            messagebox.showerror("Error", "Room not selected!")

    def display_rooms(self):
        room_name = self.room_selection.get()
        if room_name:
            cursor = self.conn.cursor()
            # Adjust the query to include the username from the meetings table
            cursor.execute(
                "SELECT meetings.date_time, meetings.username "
                "FROM meetings "
                "JOIN rooms ON meetings.room_id = rooms.id "
                "WHERE rooms.name=?", (room_name,))
            meetings = cursor.fetchall()
            self.meetings_listbox.delete(0, tk.END)
            if meetings:
                for meeting in meetings:
                    date_time, username = meeting  # Extract the username from the tuple
                    # Format the string to include the username
                    meeting_info = f"Meeting: {date_time} booked by {username}"
                    self.meetings_listbox.insert(tk.END, meeting_info)
            else:
                self.meetings_listbox.insert(
                    tk.END, "No meetings found for this room")
        else:
            messagebox.showerror("Error", "Room not selected!")

    def quit_app(self):
        self.conn.close()
        self.master.quit()

    def load_rooms(self):
        self.room_selection['values'] = ()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM rooms")
        rooms = cursor.fetchall()
        self.room_selection['values'] = [room[0] for room in rooms]


    def load_meetings(self, event=None):
        room_name = self.room_selection.get()
        if room_name:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM rooms WHERE name=?", (room_name,))
            room_id = cursor.fetchone()
            if room_id:
                selected_date = self.calendar.get_date()
                # Include the username in the SELECT statement
                cursor.execute(
                    "SELECT meetings.date_time, meetings.username "
                    "FROM meetings "
                    "WHERE date(meetings.date_time) = ? AND meetings.room_id = ?",
                    (selected_date, room_id[0])
                )
                meetings = cursor.fetchall()
                self.meetings_listbox.delete(0, tk.END)
                if meetings:
                    for meeting in meetings:
                        date_time, username = meeting  # Now you also get the username
                        # Insert both date_time and username in the listbox
                        meeting_info = f"Meeting: {date_time} booked by {username}"
                        self.meetings_listbox.insert(tk.END, meeting_info)
                else:
                    self.meetings_listbox.insert(
                        tk.END, "No meetings found for this day")
            else:
                self.meetings_listbox.delete(0, tk.END)
                self.meetings_listbox.insert(tk.END, "Room not found in database.")
        else:
            messagebox.showerror("Error", "Room not selected!")


    def highlight_dates_with_events(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT date(date_time) FROM meetings")
        dates_with_events = cursor.fetchall()
        for date_with_event in dates_with_events:
            # Parse the date string to a datetime.date instance
            date = datetime.strptime(date_with_event[0], "%Y-%m-%d").date()
            # Now, date is a datetime.date instance suitable for calevent_create
            self.calendar.calevent_create(date, text='Event', tags='event')

if __name__ == "__main__":
    root = tk.Tk()
    app = RoomBookingApp(root)
    root.mainloop()

