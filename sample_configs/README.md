# Configuration for macOS App Updater

This README provides an overview of the **sample configuration files** used with the macOS App Updater script. \

These sample configuration files contain examples of working configurations that you can customize to suit your needs. The sample configuration files are structured to include common settings, and it is **recommended** to use these as a starting point. You can simply copy a sample file and modify the fields as needed to fit your application.

## 📁 Sample Configuration Files

The configuration files are in **JSON format** and contains the following fields:

```json
{
  "name": "",
  "url": "",
  "regex": null,
  "code": null,
  "file_type": null,
  "pkg_install_path": "/",
  "app_install_path": "/Applications",
  "allow_downgrade": false,
  "reinstall": false,
  "run": false,
  "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
  "blocking_app": null,
  "blocking_file": null,
  "required_file": null,
  "blocking_app_insensitive": false,
  "log_level": 4,
  "verbosity": -1,
  "log_file": null,
  "comment": "Blank configuration. By not including a field, you use the default. By including it, you set the value. Code will be taken over regex."
}
```
## Configuration Options Explained:

- **name**: (String)  
  - The name of the application. Used for logging and identification.

- **url**: (String)  
  - The direct URL or a page URL from which the application will be downloaded.

- **regex**: (String, Nullable)  
  - A regular expression to identify the download link if the URL does not directly point to the file.

- **code**: (String, Nullable)  
  - Custom code to extract the download link if **regex** is not sufficient.  
  - **Note:** If both **regex** and **code** are provided, **code** takes precedence.

- **file_type**: (String, Nullable)  
  - Specifies the file type (e.g., **dmg**, **pkg**, **zip**). Automatically detected if left as **null**.

- **pkg_install_path**: (String)  
  - The installation path for packages. Default is **/**.

- **app_install_path**: (String)  
  - The installation path for applications. Default is **/Applications**.

- **allow_downgrade**: (Boolean)  
  - Allows the application to be downgraded if the downloaded version is older than the installed one. Default is **false**.

- **reinstall**: (Boolean)  
  - Forces reinstallation even if the version is the same. Default is **false**.

- **run**: (Boolean)  
  - Automatically runs the application after installation, if installed. Default is **false**.

- **user_agent**: (String)  
  - Specifies the **User-Agent** string to use when downloading. Default is a standard Chrome user agent.

- **blocking_app**: (String, Nullable)  
  - Specifies an application name that must not be running during installation.  
  - **Example:** `"Terminal.app"`

- **blocking_file**: (String, Nullable)  
  - Specifies a file that must not exist.

- **required_file**: (String, Nullable)  
  - Specifies a file that must exist for the application to be installed.

- **blocking_app_insensitive**: (Boolean)  
  - Determines whether the **blocking_app** name is case-insensitive. Default is **false**.

- **log_level**: (Integer)  
  - Sets the level of logging.  
    - **0:** Critical  
    - **1:** Error  
    - **2:** Warning  
    - **3:** Info  
    - **4:** Debug  
  - Default: **4**

- **log_file**: (String, Nullable)  
  - Specifies a file to log output. If **null**, logging is done to standard output.

- **comment**: (String)  
  - A description or comment about the configuration. Helpful for maintaining and understanding multiple configuration files.
## 🌟 Tips:
	1.	By omitting a field, you allow the program to use the default value.
	2.	Including a field explicitly overrides the default.
	3.	Regex vs. Code: If both are present, code takes priority as it allows for more complex extraction logic.
	4.	Use sample configuration files as templates to quickly set up new applications.

## 📝 Example Usage:
	1.	Copy a sample configuration file.
	2.	Edit the fields to suit your application.
	3.	Run the macOS App Updater with the modified configuration file.

For more details, refer to the project documentation.