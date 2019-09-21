package FauxDeviceEngine;

import org.json.simple.JSONArray;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;

public class JSON {

    private String fileName = "";

    public JSON(String fileName) {
        this.fileName = fileName;
    }

    public JSONArray read() {
        JSONParser jsonParser = new JSONParser();
        JSONArray bacnetObjectTypeList = null;
        try(FileReader reader = new FileReader(fileName)) {
            Object obj = jsonParser.parse(reader);
            bacnetObjectTypeList = (JSONArray) obj;
        } catch (FileNotFoundException e ) {
            e.printStackTrace();
            return null;
        } catch (IOException e) {
            e.printStackTrace();
            return null;
        } catch (ParseException e) {
            e.printStackTrace();
            return null;
        }
        return bacnetObjectTypeList;
    }
}
