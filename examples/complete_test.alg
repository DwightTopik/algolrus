алг полный_тест_аттестации;
нач
    число : цел;
    флаг : лог;
    символ : сим;
    строка_переменная : строка;
    массив_чисел : таб[10] цел;
    массив_символов : таб[5] сим;
    
    i : цел;
    j : цел;
    k : цел;
    результат : лог;
    temp : цел;
кон
    число := 42;
    флаг := да;
    символ := 'A';
    строка_переменная := "Привет мир!";
    
    i := 15;
    j := 4;
    число := i + j;
    число := i - j;
    число := i * j;
    число := i / j;
    число := i div j;
    число := i mod j;
    
    число := +i;
    число := -i;
    
    результат := i = j;
    результат := i <> j;
    результат := i > j;
    результат := i >= j;
    результат := i < j;
    результат := i <= j;
    
    результат := да и нет;
    результат := да или нет;
    результат := не да;
    результат := не нет;
    
    массив_чисел[1] := 100;
    массив_чисел[2] := массив_чисел[1] + 50;
    число := массив_чисел[2];
    
    массив_символов[1] := 'H';
    массив_символов[2] := 'i';
    символ := массив_символов[1];
    
    если i > j то
        вывод("i больше j");
        число := i;
    иначе
        вывод("i не больше j");
        число := j;
    все
    
    если число > 10 то
        если число > 20 то
            вывод("число больше 20");
        иначе
            вывод("число от 10 до 20");
        все
    все
    
    для i от 1 до 5
        массив_чисел[i] := i * 10;
        вывод("Заполняем массив");
    кц
    
    для i от 10 до 2 шаг -2
        число := число + i;
    кц
    
    i := 1;
    пока i <= 3
        число := число + i;
        i := i + 1;
    кц
    
    i := 1;
    цикл
        число := число * 2;
        i := i + 1;
    до i > 2
    
    для i от 1 до 10
        если i = 3 то
            далее
        все
        если i = 7 то
            стоп
        все
        массив_чисел[i] := i;
    кц
    
    для i от 1 до 3
        для j от 1 до 2
            k := i * j;
            массив_чисел[k] := k;
        кц
    кц
    
    вывод("Результат вычислений:");
    вывод(число);
    вывод("Массив:");
    для i от 1 до 5
        вывод(массив_чисел[i]);
    кц
    
    увел(число);
    умен(число);
    число := модуль(-25);
    
    число := (i + j) * (i - j);
    результат := (i > 0) и (j < 10) или не флаг;
    число := ((i + j) * 2) / (i - j + 1);
    
    russian_var := 100;
    латинская_переменная := 200;
    mixed_переменная := russian_var + латинская_переменная;
    
    увел(mixed_переменная);
    умен(mixed_переменная);
    temp := модуль(mixed_переменная - 500);
    
    вывод("=== ТЕСТ ЗАВЕРШЁН УСПЕШНО ===");
    вывод("Все обязательные возможности протестированы:");
    вывод(" Типы: цел, лог, сим, строка, массивы");
    вывод(" Операции: +, -, *, /, div, mod, =, <>, >, >=, <, <=");
    вывод(" Логика: и, или, не");
    вывод(" Управление: если-то-иначе-все");
    вывод(" Циклы: для-от-до-кц, пока-кц, цикл-до");
    вывод(" Операторы: стоп, далее");
    вывод(" Функции: вывод, увел, умен, модуль");
    вывод(" Массивы: таб[размер] тип");
    вывод(" Выражения: скобки, приоритет операций");
    вывод(" Идентификаторы: русские и латинские");
кон 