package helper;

import java.io.File;

public class FileManager {

    private String filePath = "";
    private String csvName = "pics";
    private String csvExtension = ".csv";
    private boolean debug = false;

    public boolean checkDevicePicCSV() {
        String csvFolder = getCSVPath();
        try{
            File[] listFiles = new File(csvFolder).listFiles();
            for (int i = 0; i < listFiles.length; i++) {
                if (listFiles[i].isFile()) {
                    String fileName = listFiles[i].getName();
                    if (fileName.contains(csvName)
                            && fileName.endsWith(csvExtension)) {
                        System.out.println("pics.csv file found in /config/type.");
                        setFilePath(fileName);
                        return true;
                    }
                }
            }
            String errorMessage = "pics.csv not found.\n";
            System.err.println(errorMessage);
        } catch(Exception e) {
            System.out.println("Error in reading " + csvName + csvExtension + " in " + csvFolder);
        }
        return false;
    }

    private void setFilePath(String fileName) {
        String absolute_path = getCSVPath();
        this.filePath = absolute_path + "/" + fileName;
    }

    public String getFilePath() {
        return this.filePath;
    }

    public String getAbsolutePath() {
        String absolute_path = "";
        String system_path = System.getProperty("user.dir");
        System.out.println("system_path: " + system_path);
        String[] path_arr = system_path.split("/");
        for (int count = 0; count < path_arr.length; count++) {
            if (path_arr[count].equals("bacnetTests")) {
                break;
            }
            absolute_path += path_arr[count] + "/";
        }
        return absolute_path;
    }

    public String getCSVPath() {
        if (debug) {
            return "src/main/resources";
        }
        return "/config/type";
    }
}
