package com.example.animals;

public class Puppy extends Dog {
    @Override
    public void process(String input) {
        System.out.println("Puppy processing: " + input);
    }
}
