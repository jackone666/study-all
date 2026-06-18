# Chapter 2: Preparation

> This section primarily recommends two browser-based integrated development environments for environment configuration. Whether you're using a phone, tablet, or computer, you can log in and run code anytime. Although the experience on phones and tablets might not be ideal, they are still usable.

## 1. Deepseek API Configuration (You can also choose other LLM APIs)

### 1.1 API Application

To use the large language model services provided by Deepseek, you first need an API Key. Here are the application steps:

1.  **Visit Deepseek Open Platform**
    Open your browser and visit [Deepseek Open Platform](https://platform.deepseek.com/).

    ![Deepseek Platform Homepage](../images/1_2_1.webp)

2.  **Login or Register Account**
    If you already have an account, please log in directly. If not, click the register button on the page and complete registration using your email or phone number.

3.  **Create New API Key**
    After successful login, find and click `API Keys` in the left navigation bar. On the API management page, click the `Create API key` button. Enter a name that doesn't duplicate other API keys and click create.

    ![Create New Key Button](../images/1_2_2.webp)

4.  **Save API Key**
    The system will generate a new API key for you. Please **copy immediately** and save it in a secure place.

    > Note: For security reasons, this key will only be displayed in full once. You won't be able to see it again after closing the popup.

    ![Copy and Save Key](../images/1_2_3.webp)

## 2. GitHub Codespaces Environment Configuration (Recommended)

> First, ensure you have a network environment that can smoothly access GitHub. If you cannot access it smoothly, please use Cloud Studio below.

GitHub Codespaces is a service provided by GitHub that allows developers to create, edit, and run code in the cloud. It provides a pre-configured development environment including code editor, terminal, debugging tools, etc., which can be used directly in the browser.

### 2.1 Creating Codespaces

1.  **Visit Project Address**

    Open your browser and visit [all-in-rag](https://github.com/datawhalechina/all-in-rag)

2.  **Create New Fork**
    In the upper right corner of the project page, click the `Fork` button to create a new fork. Wait a moment for successful creation.

    ![Create New Fork 1](../images/1_2_4.webp)

    ![Create New Fork 2](../images/1_2_5.webp)

3.  **Create Codespaces**
    In the upper right corner of the project page, click the `Code` button, then select the `Codespaces` tab. Click the `New codespace` button and wait for the new Codespaces environment to be created successfully.

    ![Create Codespaces](../images/1_2_6.webp)

4.  **Re-enter Codespaces**
    After closing the webpage, find the newly created repository and click the content in the red box to re-enter the codespace environment.

    ![Re-enter Codespaces](../images/1_2_7.webp)

5.  **Quota Settings**
    Find the codespace settings in GitHub's account settings. It's recommended to adjust the suspend time according to your situation (too long will waste quota, free accounts provide 120 hours of single-core quota).

    ![Quota Settings](../images/1_2_8.webp)

### 2.2 Python Environment Configuration

After entering the IDE, first select the terminal below.

![Enter Terminal](../images/1_2_9.webp)

1.  **Update System Packages**

    Enter the following command in the terminal:

    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

2.  **Install Miniconda**

    ```bash
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    bash ~/miniconda.sh
    ```

    - Press Enter to read the license agreement
    - Enter `yes` to agree to the agreement
    - Press Enter directly when prompted for installation path (use default path /home/ubuntu/miniconda3)
    - Whether to initialize Miniconda: Enter `yes` to add Miniconda to your PATH environment variable.

    ```bash
    source ~/.bashrc
    conda --version
    ```

    If the version number is displayed, the installation is successful.

### 2.3 API Configuration

1.  Use the `vim` editor to open your shell configuration file.

    ```bash
    vim ~/.bashrc
    ```

2.  Enter `i` to enter edit mode, add the following line at the end of the file, replacing `[Your Deepseek API Key]` with your own key:

    ```bash
    export DEEPSEEK_API_KEY=[Your Deepseek API Key]
    ```

3.  Save and exit. In vim, press Esc to enter command mode, then type `:wq` and press Enter to save the file and exit.

4.  Make configuration effective. Execute the following command to immediately load the updated configuration and make the environment variable effective:

    ```bash
    source ~/.bashrc
    ```

### 2.4 Create and Activate Virtual Environment

1.  **Create Virtual Environment**

    ```bash
    conda create --name all-in-rag python=3.12.7
    ```

    Press Enter directly when options appear.

2.  **Activate Virtual Environment**

    Use the following command to activate the virtual environment:

    ```bash
    conda activate all-in-rag
    ```

3.  **Dependency Installation**
    If you strictly follow the above process, you should currently be in the project root directory. Enter the code directory to install dependency libraries.

    ```bash
    cd code
    pip install -r requirements.txt
    ```

    > If there are version errors about grpcio, you can ignore them.

## 3. Cloud Studio Environment Configuration (Recommended for Domestic Environment)

Cloud Studio is a browser-based integrated development environment (IDE) launched by Tencent Cloud. It supports access to both CPU and GPU.

> I heard there's a free quota of 50 hours per month 🤔

### 3.1 Application Creation

1.  **Visit Cloud Studio**
    Open your browser and visit [Cloud Studio](https://cloudstudio.net/).

2.  **Login or Register Account**
    Click the `Register/Login` button in the upper right corner of the page and complete login using WeChat or other methods.

3.  **Create Application**
    Find and click `Create Application` in the navigation bar at the top of the page. Select `Import from Git Repository`, enter `https://github.com/datawhalechina/all-in-rag.git` in the project address bar and press Enter. It will automatically create a title and description for you.

    ![Create Application](../images/1_2_10.webp)

4.  **Re-enter**
    Later, find the previously created application on the [Application Management Page](https://cloudstudio.net/my-app), click on it and select "Write Code" in the upper right corner to re-enter.

    ![Re-enter Application](../images/1_2_11.webp)

### 3.2 Python Environment Configuration

After entering the IDE, first select the terminal on the right.

![Enter Terminal](../images/1_2_12.webp)

1.  **Update System Packages**

    Enter the following command in the terminal:

    ```bash
    sudo apt update
    sudo apt upgrade -y
    ```

2.  **Switch to Regular User**

    ```bash
    su ubuntu
    ```

3.  **Install Miniconda**

    ```bash
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh
    bash ~/miniconda.sh
    ```

    - Press Enter to read the license agreement
    - Enter `yes` to agree to the agreement
    - Press Enter directly when prompted for installation path (use default path /home/ubuntu/miniconda3)
    - Whether to initialize Miniconda: Enter `yes` to add Miniconda to your PATH environment variable.

    ```bash
    source ~/.bashrc
    conda --version
    ```

    If the version number is displayed, the installation is successful.

### 3.3 API Configuration

1.  Use the `vim` editor to open your shell configuration file.

    ```bash
    vim ~/.bashrc
    ```

2.  Enter `i` to enter edit mode, add the following line at the end of the file, replacing `[Your Deepseek API Key]` with your own key:

    ```bash
    export DEEPSEEK_API_KEY=[Your Deepseek API Key]
    ```

3.  Save and exit. In vim, press Esc to enter command mode, then type `:wq` and press Enter to save the file and exit.

4.  Make configuration effective. Execute the following command to immediately load the updated configuration and make the environment variable effective:

    ```bash
    source ~/.bashrc
    ```

### 3.4 Create and Activate Virtual Environment

1.  **Create Virtual Environment**

    ```bash
    conda create --name all-in-rag python=3.12.7
    ```

    Press Enter directly when options appear.

2.  **Configure File Permissions**

    ```bash
    sudo chown -R ubuntu:ubuntu code models
    ```

3.  **Activate Virtual Environment**

    Use the following command to activate the virtual environment:

    ```bash
    conda activate all-in-rag
    ```

4.  **Dependency Installation**
    If you strictly follow the above process, you should currently be in the project root directory. Enter the code directory to install dependency libraries.

    ```bash
    cd code
    pip install -r requirements.txt
    ```

    > If there are version errors about grpcio, you can ignore them.

## 4. Windows Environment Configuration (Skip this step if using Cloud Studio or Codespaces)

### 4.1 API Configuration

1.  Right-click "Computer" or "This PC", then click "Properties".

2.  In the left menu, click "Advanced system settings".

3.  In the "System Properties" dialog box, click the "Advanced" tab, then click the "Environment Variables" button below.

    ![Advanced System Settings](../images/1_2_13.webp)

4.  In the "Environment Variables" dialog box, click "New" (under the "User variables" section), then enter the following information:
    - Variable name: DEEPSEEK_API_KEY
    - Variable value: [Your Deepseek API Key]

    ![Advanced System Settings](../images/1_2_14.webp)

### 4.2 Install Miniconda

1.  **Download Installer**

    It's recommended to visit [Tsinghua University Open Source Software Mirror](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/) for faster download speeds. Choose the latest `Windows-x86_64.exe` version according to your system.

    ![Select Miniconda Version](images/ch1/miniconda-select-version.png)

    You can also download from the [Miniconda Official Website](https://docs.conda.io/en/latest/miniconda.html).

2.  **Run Installation Wizard**

    After downloading, double-click the `.exe` file to start installation. Follow the wizard prompts:

    *   **Welcome**: Click `Next`.
        ![Welcome](../images/)
    *   **License Agreement**: Click `I Agree`.
        ![License Agreement](../images/)
    *   **Installation Type**: Select `Just Me`, click `Next`.
        ![Installation Type](../images/)
    *   **Choose Install Location**: It's recommended to keep the default path, or choose a path without Chinese characters and spaces. Click `Next`.
        ![Install Location](../images/)
    *   **Advanced Installation Options**: **Do not check** "Add Miniconda3 to my PATH environment variable". We will manually configure environment variables later. Click `Install`.
        ![Advanced Options](../images/)
    *   **Installation Complete**: After installation is complete, click `Next`, then uncheck "Learn more" and click `Finish` to complete installation.
        ![Installation Complete](../images/)

3.  **Manually Configure Environment Variables**

    To use the `conda` command in any terminal window, you need to manually configure environment variables.

    *   Search for "Edit the system environment variables" in the Windows search bar and open it.
        ![Edit System Environment Variables](../images/)
    *   In the "System Properties" window, click "Environment Variables".
        ![Environment Variables Button](../images/)
    *   In the "Environment Variables" window, find the `Path` variable under "System variables", select it and click "Edit".
        ![Edit Path Variable](../images/)
    *   In the "Edit Environment Variable" window, create three new paths pointing to the corresponding folders under your Miniconda installation directory. If your installation path is `D:\Miniconda3`, you need to add:
        ```
        D:\Miniconda3
        D:\Miniconda3\Scripts
        D:\Miniconda3\Library\bin
        ```
        ![Add Paths](../images/)
    *   After completion, click "OK" all the way to save changes.

### 4.3 Configure Conda Mirror Sources

To speed up subsequent package installations using `conda`, it's strongly recommended to configure domestic mirror sources. Open a new terminal or Anaconda Prompt and run the following commands:

```bash
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --set show_channel_urls yes
```

After configuration, you can view the added sources using the `conda config --show channels` command.

## 5. Project Code Pulling (Skip this step if using Cloud Studio or Codespaces)

### 5.1 Install Git

If you haven't installed Git yet, please follow these steps to install it.

* **Windows System**: Visit the [Git Official Website](https://git-scm.com/download/win), download and run the installer, complete installation with default settings.
* **macOS System**: Open terminal and enter the following command to install Git:

  ```bash
  brew install git
  ```
* **Linux System (Ubuntu example)**: Open terminal and enter the following commands to install Git:

  ```bash
  sudo apt-get update
  sudo apt-get install git
  ```

After installation, verify that Git is installed successfully by entering the following command:

```bash
git --version
```

If successful, it will display Git's version number.

### 5.2 Clone Project Code

1. **Choose Directory for Project**
   Open terminal (or Git Bash in Windows), navigate to the directory where you want to store the project:

   ```bash
   cd [path where you want to store the project]
   ```

2. **Clone Repository**
   Use the following command to pull the `all-in-rag` repository:

   ```bash
   git clone https://github.com/datawhalechina/all-in-rag.git
   ```

   Wait for the download to complete. The project code will be stored in the `all-in-rag` folder in the current directory.

3. **Enter Project Directory**
   After pulling the code, enter the project directory:

   ```bash
   cd all-in-rag
   ```

### 5.3 Create and Activate Virtual Environment

In the project directory, it's recommended to use the previously configured Miniconda to create a Python virtual environment.

1. **Create Virtual Environment**

   ```bash
   conda create --name all-in-rag python=3.12.7
   ```

2. **Activate Virtual Environment**

   All systems use the following command to activate the virtual environment:

   ```bash
   conda activate all-in-rag
   ```

3.  **Dependency Installation**
    If you strictly follow the above process, you should currently be in the project root directory. Enter the code directory to install dependency libraries.

    ```bash
    cd code
    pip install -r requirements.txt
    ```