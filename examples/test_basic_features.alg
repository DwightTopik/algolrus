алг тест_основы;
нач
    число : цел;
    флаг : лог;
    символ : сим;
    массив : таб[5] цел;
    строка_переменная : строка;
кон
    число := 42;
    флаг := да;
    символ := 'A';
    строка_переменная := "Привет";
    
    число := 10 + 3;
    число := 10 - 3;
    число := 10 * 3;
    число := 10 / 3;
    число := 10 div 3;
    число := 10 mod 3;
    
    число := +10;
    число := -10;
    
    флаг := 10 = 3;
    флаг := 10 <> 3;
    флаг := 10 > 3;
    флаг := 10 >= 3;
    флаг := 10 < 3;
    флаг := 10 <= 3;
    
    флаг := да и нет;
    флаг := да или нет;
    флаг := не да;
    
    массив[1] := 100;
    массив[2] := массив[1] + 50;
    число := массив[2];
    
    если число > 0 то
        вывод("Число положительное");
    иначе
        вывод("Число не положительное");
    все
    
    для число от 1 до 3
        вывод("Итерация цикла");
    кц
    
    число := 1;
    пока число <= 2
        число := число + 1;
    кц
    
    число := 1;
    цикл
        число := число + 1;
    пока число <= 2
    
    вывод("Результат");
    увел(число);
    умен(число);
    число := модуль(-5);
    
    число := (10 + 3) * (10 - 3);
    флаг := (число > 0) и (число < 100) или не флаг;
кон 