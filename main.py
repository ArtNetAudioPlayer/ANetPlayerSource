import tkinter as tk
import tkinter.messagebox as tkMessageBox
import artnetplayer


def ask_quit():
    # Confirmation to quit application.
    if tkMessageBox.askokcancel("Quit", "Exit Art-Net Audio Player?"):
        try:
            app.stop()  # Stop playing track
            app.player.quit()  # Quit pygame.mixer
            root.destroy()  # Destroy the Tk Window instance.
        except TypeError:
            print("TypeError")
            app.player.quit()
            root.destroy()


if __name__ == "__main__":
    # Initialize an instance of Tk window.
    root = tk.Tk()
    # Initialize an instance of MusicPlayer object and passing Tk window instance into it as it's master.
    app = artnetplayer.ArtNetPlayer(root)
    app.create_widgets()
    root.protocol("WM_DELETE_WINDOW", ask_quit)  # Tell Tk window instance what to do before it is destroyed.
    root.mainloop()
