from chat_interface import create_interface

def main():
    """Main function to launch the Gradio interface"""
    demo = create_interface()
    demo.launch()

if __name__ == "__main__":
    main()