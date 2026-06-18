# Java集合

> 重要性等级：S=至尊（必考，频率>80%） A=高级（高频，频率50%-80%） B=基础（中频，频率30%-50%） C=普通（低频，<30%）

# 概念

## 数组与集合区别，用过哪些？ [重要性:B]

数组和集合的区别：

- 数组是固定长度的数据结构，一旦创建长度就无法改变，而集合是动态长度的数据结构，可以根据需要动态增加或减少元素。
- 数组可以包含基本数据类型和对象，而集合只能包含对象。
- 数组可以直接访问元素，而集合需要通过迭代器或其他方法访问元素。

我用过的一些 Java 集合类：

- **ArrayList**：动态数组，实现了 List 接口，支持动态增长。
- **LinkedList**：双向链表，也实现了 List 接口，支持快速的插入和删除操作。
- **HashMap**：基于哈希表的 Map 实现，存储键值对，通过键快速查找值。
- **HashSet**：基于 HashMap 实现的 Set 集合，用于存储唯一元素。
- **TreeMap**：基于红黑树实现的有序 Map 集合，可以按照键的顺序进行排序。
- **LinkedHashMap**：基于哈希表和双向链表实现的 Map 集合，保持插入顺序或访问顺序。
- **PriorityQueue**：优先队列，可以按照比较器或元素的自然顺序进行排序。

---

## 说说Java中的集合？ [重要性:S]

**List** 是有序的 Collection，使用此接口能够精确的控制每个元素的插入位置，用户能根据索引访问 List 中元素。常用的实现 List 的类有 LinkedList，ArrayList，Vector，Stack。

- **ArrayList** 是容量可变的非线程安全列表，其底层使用数组实现。当集合扩容时，会创建更大的数组，并把原数组复制到新数组。ArrayList 支持对元素的快速随机访问，在尾部追加/删除元素效率很高，但在中间位置插入/删除需要搬移元素，代价较高。
- **LinkedList** 本质是一个双向链表，支持高效的头尾插入/删除和作为双端队列使用。需要注意的是："LinkedList 插入/删除比 ArrayList 更快"是一个常见误区：其 O(1) 的前提是已经持有目标节点的引用；如果要在任意位置插入/删除，仍需先 O(n) 遍历链表找到位置，加上每个节点都需要独立分配、对 CPU 缓存不友好，实测大多数场景下 LinkedList 反而比 ArrayList 慢，这也是现在主流建议优先使用 ArrayList 的原因。

**Set** 不允许存在重复的元素，与 List 不同，set 中的元素是无序的。常用的实现有 HashSet，LinkedHashSet 和 TreeSet。

- **HashSet** 通过 HashMap 实现，HashMap 的 Key 即 HashSet 存储的元素，所有 Key 都是用相同的 Value，一个名为 PRESENT 的 Object 类型常量。使用 Key 保证元素唯一性，但不保证有序性。由于其底层的 HashMap 本身就是非线程安全的，因此 HashSet 也是非线程安全的。
- **LinkedHashSet** 继承自 HashSet，通过 LinkedHashMap 实现，使用双向链表维护元素插入顺序。
- **TreeSet** 通过 TreeMap 实现的，添加元素到集合时按照比较规则将其插入合适的位置，保证插入后的集合仍然有序。

**Map** 是一个键值对集合，存储键、值和之间的映射。Key 无序，唯一；value 不要求有序，允许重复。Map 没有继承于 Collection 接口，从 Map 集合中检索元素时，只要给出键对象，就会返回对应的值对象。主要实现有 TreeMap、HashMap、Hashtable、LinkedHashMap、ConcurrentHashMap。

- **HashMap**：JDK1.8 之前 HashMap 由数组+链表组成的，数组是 HashMap 的主体，链表则是主要为了解决哈希冲突而存在的（"拉链法"解决冲突），JDK1.8 以后在解决哈希冲突时有了较大的变化：当某个桶的链表长度 ≥ 8 且哈希表数组长度 ≥ 64 时，才会将该链表转化为红黑树，以减少搜索时间；如果数组长度 < 64，则只会触发扩容而不做树化。
- **LinkedHashMap**：LinkedHashMap 继承自 HashMap，所以它的底层仍然是基于拉链式散列结构即由数组和链表或红黑树组成。另外，LinkedHashMap 在上面结构的基础上，增加了一条双向链表，使得上面的结构可以保持键值对的插入顺序。同时通过对链表进行相应的操作，实现了访问顺序相关逻辑。
- **Hashtable**：数组+链表组成的，数组是 Hashtable 的主体，链表则是主要为了解决哈希冲突而存在的。
- **TreeMap**：红黑树（自平衡的排序二叉树）。
- **ConcurrentHashMap**：Node 数组+链表+红黑树实现，线程安全的（jdk1.8 以前 Segment 锁，1.8 以后 volatile + CAS 或者 synchronized）。

![Java集合框架总览](zmedia/Java集合面试题_images/02_java_collections_overview.webp)

---

## Java中的线程安全的集合是什么？ [重要性:S]

在 `java.util` 包中的线程安全的类主要 2 个，其他都是非线程安全的。

- **Vector**：线程安全的动态数组，其内部方法基本都经过 synchronized 修饰，如果不需要线程安全，并不建议选择，毕竟同步是有额外开销的。Vector 内部是使用对象数组来保存数据，可以根据需要自动的增加容量，当数组已满时，会创建新的数组，并拷贝原有数组数据。
- **Hashtable**：线程安全的哈希表，Hashtable 的加锁方法是给每个方法加上 synchronized 关键字，这样锁住的是整个 Table 对象，不支持 null 键和值，由于同步导致的性能开销，所以已经很少被推荐使用，如果要保证线程安全的哈希表，可以用 ConcurrentHashMap。

`java.util.concurrent` 包提供的都是线程安全的集合：

- **并发 Map**：
  - **ConcurrentHashMap**：它与 Hashtable 的主要区别是二者加锁粒度的不同，在 JDK 1.7，ConcurrentHashMap 加的是分段锁，也就是 Segment 锁，每个 Segment 含有整个 table 的一部分，这样不同分段之间的并发操作就互不影响。在 JDK 1.8，它取消了 Segment，直接在 table 元素（桶的头节点）上加锁，使加锁粒度进一步缩小到单个桶级别。对于 put 操作，如果 Key 对应的数组槽位为 null，则通过 CAS 操作（Compare and Swap）将新节点写入该槽位；如果槽位不为 null（即已存在链表头或红黑树根节点），则对该头节点使用 synchronized 加锁，然后遍历桶中的数据执行替换或新增。如果该 put 操作使得当前桶的链表长度超过阈值，则将其转换为红黑树，从而提高查找效率。
  - **ConcurrentSkipListMap**：实现了一个基于 SkipList（跳表）算法的可排序的并发集合，SkipList 是一种可以在对数预期时间内完成搜索、插入、删除等操作的数据结构，通过维护多个指向其他元素的"跳跃"链接来实现高效查找。
- **并发 Set**：
  - **ConcurrentSkipListSet**：是线程安全的有序的集合。底层是使用 ConcurrentSkipListMap 实现。
  - **CopyOnWriteArraySet**：是线程安全的 Set 实现，它是线程安全的无序的集合，可以将它理解成线程安全的 HashSet。有意思的是，CopyOnWriteArraySet 和 HashSet 虽然都继承于共同的父类 AbstractSet；但是，HashSet 是通过"散列表"实现的，而 CopyOnWriteArraySet 则是通过"动态数组(CopyOnWriteArrayList)"实现的，并不是散列表。
- **并发 List**：
  - **CopyOnWriteArrayList**：它是 ArrayList 的线程安全的变体，其中所有写操作（add，set 等）都通过对底层数组进行全新复制来实现，允许存储 null 元素。即当对象进行写操作时，使用了 Lock 锁做同步处理，内部拷贝了原数组，并在新数组上进行添加操作，最后将新数组替换掉旧数组；若进行的读操作，则直接返回结果，操作过程中不需要进行同步。
- **并发 Queue**：
  - **ConcurrentLinkedQueue**：是一个适用于高并发场景下的队列，它通过无锁的方式(CAS)，实现了高并发状态下的高性能。通常，ConcurrentLinkedQueue 的性能要好于 BlockingQueue。
  - **BlockingQueue**：与 ConcurrentLinkedQueue 的使用场景不同，BlockingQueue 的主要功能并不是在于提升高并发时的队列性能，而在于简化多线程间的数据共享。BlockingQueue 提供一种读写阻塞等待的机制，即如果消费者速度较快，则 BlockingQueue 则可能被清空，此时消费线程再试图从 BlockingQueue 读取数据时就会被阻塞。反之，如果生产线程较快，则 BlockingQueue 可能会被装满，此时，生产线程再试图向 BlockingQueue 队列装入数据时，便会被阻塞等待。
- **并发 Deque**：
  - **LinkedBlockingDeque**：是一个线程安全的双端队列实现。它的内部使用链表结构，每一个节点都维护了一个前驱节点和一个后驱节点。LinkedBlockingDeque 没有进行读写锁的分离，因此同一时间只能有一个线程对其进行操作。
  - **ConcurrentLinkedDeque**：ConcurrentLinkedDeque 是一种基于链接节点的无限并发链表。可以安全地并发执行插入、删除和访问操作。当许多线程同时访问一个公共集合时，ConcurrentLinkedDeque 是一个合适的选择。

---

## Collections和Collection的区别 [重要性:B]

- **Collection** 是 Java 集合框架中的一个接口，它是所有集合类的基础接口。它定义了一组通用的操作和方法，如添加、删除、遍历等，用于操作和管理一组对象。Collection 接口有许多实现类，如 List、Set 和 Queue 等。
- **Collections**（注意有一个 s）是 Java 提供的一个工具类，位于 `java.util` 包中。它提供了一系列静态方法，用于对集合进行操作和算法。Collections 类中的方法包括排序、查找、替换、反转、随机化等等。这些方法可以对实现了 Collection 接口的集合进行操作，如 List 和 Set。

---

## 集合遍历的方法有哪些？ [重要性:B]

在 Java 中，集合的遍历方法主要有以下几种：

**1. 普通 for 循环**：可以使用带有索引的普通 for 循环来遍历 List。

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

for (int i = 0; i < list.size(); i++) {
    String element = list.get(i);
    System.out.println(element);
}
```

**2. 增强 for 循环（for-each 循环）**：用于循环访问数组或集合中的元素。

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

for (String element : list) {
    System.out.println(element);
}
```

**3. Iterator 迭代器**：可以使用迭代器来遍历集合，特别适用于需要删除元素的情况。

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

Iterator<String> iterator = list.iterator();
while(iterator.hasNext()) {
    String element = iterator.next();
    System.out.println(element);
}
```

**4. ListIterator 列表迭代器**：ListIterator 是迭代器的子类，可以双向访问列表并在迭代过程中修改元素。

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

ListIterator<String> listIterator= list.listIterator();
while(listIterator.hasNext()) {
    String element = listIterator.next();
    System.out.println(element);
}
```

**5. 使用 forEach 方法**：Java 8 引入了 forEach 方法，可以对集合进行快速遍历。

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

list.forEach(element -> System.out.println(element));
```

**6. Stream API**：Java 8 的 Stream API 提供了丰富的功能，可以对集合进行函数式操作，如过滤、映射等。

```java
List<String> list = new ArrayList<>();
list.add("A");
list.add("B");
list.add("C");

list.stream().forEach(element -> System.out.println(element));
```

---

# List

![List 继承层次结构](zmedia/Java集合面试题_images/03_list_hierarchy.png)

常见的 List 集合（非线程安全）：

- **ArrayList** 基于动态数组实现，它允许快速的随机访问，即通过索引访问元素的时间复杂度为 O(1)。在添加和删除元素时，如果操作位置不是列表末尾，可能需要移动大量元素，性能相对较低。适用于需要频繁随机访问元素，而对插入和删除操作性能要求不高的场景，如数据的查询和展示等。
- **LinkedList** 基于双向链表实现，在插入和删除元素时，只需修改链表的指针，不需要移动大量元素，时间复杂度为 O(1)。但随机访问元素时，需要从链表头或链表尾开始遍历，时间复杂度为 O(n)。适用于需要频繁进行插入和删除操作的场景，如队列、栈等数据结构的实现，以及需要在列表中间频繁插入和删除元素的情况。

常见的 List 集合（线程安全）：

- **Vector** 和 ArrayList 类似，也是基于数组实现。Vector 中的方法大多是同步的，这使得它在多线程环境下可以保证数据的一致性，但在单线程环境下，由于同步带来的开销，性能会略低于 ArrayList。
- **CopyOnWriteArrayList** 在对列表进行修改（如添加、删除元素）时，会创建一个新的底层数组，将修改操作应用到新数组上，而读操作仍然在原数组上进行，这样可以保证读操作不会被写操作阻塞，实现了读写分离，提高了并发性能。适用于读操作远远多于写操作的并发场景，如事件监听列表等。

---

## 讲一下java里面list的几种实现，几种实现有什么不同？ [重要性:A]

在 Java 中，List 接口是最常用的集合类型之一，用于存储元素的有序集合。以下是 Java 中常见的 List 实现及其特点：

- **Vector** 是 Java 早期提供的线程安全的动态数组，如果不需要线程安全，并不建议选择，毕竟同步是有额外开销的。Vector 内部是使用对象数组来保存数据，可以根据需要自动的增加容量，当数组已满时，会创建新的数组，并拷贝原有数组数据。
- **ArrayList** 是应用更加广泛的动态数组实现，它本身不是线程安全的，所以性能要好很多。与 Vector 近似，ArrayList 也是可以根据需要调整容量，不过两者的调整逻辑有所区别：Vector 默认按 2 倍扩容（如果构造时指定了 capacityIncrement，则按该值线性增长），而 ArrayList 则是增加 50%（即 1.5 倍）。
- **LinkedList** 顾名思义是 Java 提供的双向链表，所以它不需要像上面两种那样调整容量，它也不是线程安全的。

**使用场景**：

- **Vector 和 ArrayList** 作为动态数组，其内部元素以数组形式顺序存储的，所以非常适合随机访问的场合。除了尾部插入和删除元素，往往性能会相对较差，比如我们在中间位置插入一个元素，需要移动后续所有元素。
- **LinkedList** 进行节点插入、删除却要高效得多，但是随机访问性能则要比动态数组慢。

![List 实现对比](zmedia/Java集合面试题_images/04_list_impl_comparison.png)

---

## list可以一边遍历一边修改元素吗？ [重要性:A]

在 Java 中，List 在遍历过程中是否可以修改元素取决于遍历方式和具体的 List 实现类：

**1. 使用普通 for 循环遍历**：可以在遍历过程中修改元素，只要修改的索引不超出 List 的范围即可。

```java
import java.util.ArrayList;
import java.util.List;

public class ListTraversalAndModification {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 使用普通for循环遍历并修改元素
        for (int i = 0; i < list.size(); i++) {
            list.set(i, list.get(i) * 2);
        }

        System.out.println(list);
    }
}
```

**2. 使用 foreach 循环遍历**：一般不建议在 foreach 循环中直接修改集合结构（add/remove），因为 foreach 底层基于迭代器实现，集合结构被修改后，迭代器下一次调用 next() 时会检测到 modCount != expectedModCount，从而抛出 `ConcurrentModificationException` 异常。注意："替换元素值"（即 `list.set(i, newValue)`）并不会改变 modCount，所以 `list.set()` 本身不会抛 CME；但 `list.add()` / `list.remove()` 会。

```java
import java.util.ArrayList;
import java.util.List;

public class ListTraversalAndModification {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);
        list.add(4);

        // 在foreach中调用list.add/remove会抛出ConcurrentModificationException
        for (Integer num : list) {
            if (num == 2) {
                list.remove(num); // 修改了结构，下一次迭代会抛CME
            }
        }

        System.out.println(list);
    }
}
```

**3. 使用迭代器遍历时**：如果需要在遍历过程中删除元素，应使用 `Iterator.remove()`；如果需要替换元素，使用 `ListIterator.set()` 是最通用、最推荐的做法。

```java
import java.util.ArrayList;
import java.util.ListIterator;

public class ListTraversalAndModification {
    public static void main(String[] args) {
        ArrayList<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 使用 ListIterator 遍历并修改元素
        ListIterator<Integer> iterator = list.listIterator();
        while (iterator.hasNext()) {
            Integer num = iterator.next();
            if (num.equals(2)) {
                // 使用 ListIterator 的 set 方法修改（替换）元素
                iterator.set(4);
            }
        }
        
        System.out.println(list); // 输出: [1, 4, 3]
    }
}
```

对于线程安全的 List，如 CopyOnWriteArrayList，由于其采用了写时复制的机制，在遍历的同时可以进行修改操作，不会抛出 `ConcurrentModificationException` 异常，但可能会读取到旧的数据，因为修改操作是在新的副本上进行的。

---

## list如何快速删除某个指定下标的元素？ [重要性:B]

**ArrayList** 提供了 `remove(int index)` 方法来删除指定下标的元素，该方法在删除元素后，会将后续元素向前移动，以填补被删除元素的位置。如果删除的是列表末尾的元素，时间复杂度为 O(1)；如果删除的是列表中间的元素，时间复杂度为 O(n)。

```java
import java.util.ArrayList;
import java.util.List;

public class ArrayListRemoveExample {
    public static void main(String[] args) {
        List<Integer> list = new ArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 删除下标为1的元素
        list.remove(1);

        System.out.println(list);
    }
}
```

**LinkedList** 的 `remove(int index)` 方法也可以用来删除指定下标的元素。它需要先遍历到指定下标位置，然后修改链表的指针来删除元素。时间复杂度为 O(n)。不过，如果已知要删除的元素是链表的头节点或尾节点，可以直接通过修改头指针或尾指针来实现删除，时间复杂度为 O(1)。

```java
import java.util.LinkedList;
import java.util.List;

public class LinkedListRemoveExample {
    public static void main(String[] args) {
        List<Integer> list = new LinkedList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 删除下标为1的元素
        list.remove(1);

        System.out.println(list);
    }
}
```

**CopyOnWriteArrayList** 的 remove 方法同样可以删除指定下标的元素。由于 CopyOnWriteArrayList 在写操作时会创建一个新的数组，所以删除操作的时间复杂度取决于数组的复制速度，通常为 O(n)。但在并发环境下，它的删除操作不会影响读操作，具有较好的并发性能。

```java
import java.util.concurrent.CopyOnWriteArrayList;

public class CopyOnWriteArrayListRemoveExample {
    public static void main(String[] args) {
        CopyOnWriteArrayList<Integer> list = new CopyOnWriteArrayList<>();
        list.add(1);
        list.add(2);
        list.add(3);

        // 删除下标为1的元素
        list.remove(1);

        System.out.println(list);
    }
}
```

---

## Arraylist和LinkedList的区别，哪个集合是线程安全的？ [重要性:S]

ArrayList 和 LinkedList 都是 Java 中常见的集合类，它们都实现了 List 接口。

- **底层数据结构不同**：ArrayList 使用动态数组实现，通过索引可以快速定位到元素。LinkedList 使用双向链表实现，每个节点都存储了元素本身以及指向前一个和后一个节点的指针。
- **插入和删除操作的效率不同**：ArrayList 在尾部进行插入和删除操作时效率较高；但如果在中间或开头插入、删除，就需要移动后面的所有元素，效率会比较低。LinkedList 在头部和尾部进行插入、删除操作时效率很高，只需要调整节点的指针即可；但如果是在中间位置操作，需要先从头或尾遍历链表找到目标位置，时间复杂度也是 O(n)。LinkedList 实现了 Deque 接口，还可以当作双端队列、栈来使用。
- **随机访问的效率不同**：ArrayList 支持通过索引直接快速访问元素，时间复杂度为 O(1)。LinkedList 不支持随机访问，必须从头节点或尾节点开始逐个遍历，时间复杂度为 O(n)。
- **空间占用**：ArrayList 只需要存储元素本身。LinkedList 每个节点除了存储元素，还需要额外存储两个指针，所以在存储相同数量元素的情况下，LinkedList 的空间占用通常会比 ArrayList 更大一些。
- **使用场景**：ArrayList 更适合需要频繁随机访问元素，或者主要在尾部进行插入、删除操作的场景。LinkedList 更适合需要频繁在头部或尾部进行插入、删除操作，或者需要作为双端队列、栈使用的场景。
- **线程安全**：这两个集合都不是线程安全的。如果在多线程环境下使用，需要自己加锁保证线程安全，或者使用线程安全的 List 集合，比如 Vector、Collections.synchronizedList() 包装的 List，或者 CopyOnWriteArrayList。

---

## arraylist和vector 区别是什么？ [重要性:A]

ArrayList 和 Vector 都是 Java 中常用的动态数组实现，但它们在设计上有几个关键区别：

1. **线程安全性**（最核心的区别）：Vector 是线程安全的，它的大部分方法（如 add、remove、get 等）都被 synchronized 修饰。而 ArrayList 没有任何同步机制，是非线程安全的。

2. **性能**：由于 Vector 的方法需要加锁释放锁，在单线程环境下，它的操作效率通常比 ArrayList 低。

3. **扩容机制**：
   - Vector 默认的扩容策略是翻倍（如果没有指定容量增量的话）。
   - ArrayList 默认扩容为原来的 1.5 倍（`newCapacity = oldCapacity + (oldCapacity >> 1)`），相对来说扩容幅度更小，能在一定程度上节省内存空间。
   - Vector 可以通过构造方法指定容量增量 `capacityIncrement`（按固定数值线性增长），而 ArrayList 没有这个功能。

---

## ArrayList线程安全吗？把ArrayList变成线程安全有哪些方法？ [重要性:S]

不是线程安全的。将 ArrayList 变成线程安全的方式有：

```java
// 1. 使用Collections类的synchronizedList方法将ArrayList包装成线程安全的List
List<String> synchronizedList = Collections.synchronizedList(arrayList);

// 2. 使用CopyOnWriteArrayList类代替ArrayList
CopyOnWriteArrayList<String> copyOnWriteArrayList = new CopyOnWriteArrayList<>(arrayList);

// 3. 使用Vector类代替ArrayList
Vector<String> vector = new Vector<>(arrayList);
```

---

## 为什么ArrayList不是线程安全的，具体来说是哪里不安全？ [重要性:S]

在高并发添加数据下，ArrayList 会暴露三个问题：

1. **部分值为 null**（我们并没有 add null 进去）
2. **索引越界异常**
3. **size 与我们 add 的数量不符**

ArrayList 的 `add` 方法代码：

```java
public boolean add(E e) {
    ensureCapacityInternal(size + 1);  // Increments modCount!!
    elementData[size++] = e;
    return true;
}
```

大致可以分为三步：
1. 判断数组需不需要扩容，如果需要的话，调用 grow 方法进行扩容；
2. 将数组的 size 位置设置值（因为数组的下标是从0开始的）；
3. 将当前集合的大小加 1。

**三种情况分析**：

- **部分值为 null**：当线程 1 发现 size 是 9，数组容量是 10，不用扩容，此时 CPU 让出执行权，线程 2 也发现 size 是 9 不用扩容。线程 1 将数组下标索引为 9 的位置 set 值了，还没有来得及执行 size++，线程 2 又把数组下标索引为 9 的位置 set 了一遍，两个线程先后进行 size++，导致下标索引 10 的地方就为 null 了。

- **索引越界异常**：线程 1 走到扩容发现 size 是 9，数组容量是 10 不用扩容，CPU 让出执行权，线程 2 也发现不用扩容。线程 1 set 完之后 size++，这时候线程 2 再进来 size 就是 10，数组的大小只有 10，而你要设置下标索引为 10 的就会越界。

- **size 与我们 add 的数量不符**：因为 size++ 本身就不是原子操作，可以分为三步：获取 size 的值，将 size 的值加 1，将新的 size 值覆盖掉原来的。线程 1 和线程 2 拿到一样的 size 值加完了同时覆盖，就会导致一次没有加上。

---

## ArrayList 和 LinkedList 的应用场景？ [重要性:A]

- **ArrayList** 适用于需要频繁访问集合元素的场景。它基于数组实现，可以通过索引快速访问元素，因此在按索引查找、遍历和随机访问元素的操作上具有较高的性能。当需要频繁访问和遍历集合元素，并且集合大小不经常改变时，推荐使用 ArrayList。
- **LinkedList** 适用于频繁进行插入和删除操作的场景。它基于链表实现，插入和删除元素的操作只需要调整节点的指针，因此在插入和删除操作上具有较高的性能。当需要频繁进行插入和删除操作，或者集合大小经常改变时，可以考虑使用 LinkedList。

---

## ArrayList的扩容机制说一下 [重要性:S]

ArrayList 在添加元素时，如果当前元素个数已经达到了内部数组的容量上限，就会触发扩容操作。主要步骤包括：

1. **计算新的容量**：一般情况下，新的容量会扩大为原容量的 1.5 倍（`newCapacity = oldCapacity + (oldCapacity >> 1)`），然后检查是否超过了最大容量限制。
2. **创建新的数组**：根据计算得到的新容量，创建一个新的更大的数组。
3. **将元素复制**：将原来数组中的元素逐个复制到新数组中。
4. **更新引用**：将 ArrayList 内部指向原数组的引用指向新数组。
5. **完成扩容**：扩容完成后，可以继续添加新元素。

扩容涉及数组的复制和内存的重新分配，所以在频繁添加大量元素时，扩容操作可能会影响性能。为了减少扩容带来的性能损耗，可以在初始化 ArrayList 时预分配足够大的容量。

之所以扩容是 1.5 倍，是因为 1.5 可以充分利用移位操作，减少浮点数或者运算时间和运算次数：

```java
// 新容量计算
int newCapacity = oldCapacity + (oldCapacity >> 1);
```

![ArrayList 扩容机制](zmedia/Java集合面试题_images/05_arraylist_grow.webp)
*ArrayList 扩容示意图*

![ArrayList 扩容细节](zmedia/Java集合面试题_images/06_arraylist_grow2.webp)

---

## 线程安全的 List，CopyonWriteArraylist是如何实现线程安全的 [重要性:A]

CopyOnWriteArrayList 底层也是通过一个数组保存数据，使用 volatile 关键字修饰数组，保证当前线程对数组对象重新赋值后，其他线程可以及时感知到。

```java
private transient volatile Object[] array;
```

**写入操作**时，加了一把互斥锁 `ReentrantLock` 以保证线程安全：

```java
public boolean add(E e) {
    //获取锁
    final ReentrantLock lock = this.lock;
    //加锁
    lock.lock();
    try {
        //获取到当前List集合保存数据的数组
        Object[] elements = getArray();
        //获取该数组的长度
        int len = elements.length;
        //将当前数组拷贝一份的同时，让其长度加1
        Object[] newElements = Arrays.copyOf(elements, len + 1);
        //将加入的元素放在新数组最后一位
        newElements[len] = e;
        //替换引用，将数组的引用指向给新数组的地址
        setArray(newElements);
        return true;
    } finally {
        //释放锁
        lock.unlock();
    }
}
```

在替换地址操作之前，读取的是老数组的数据；执行替换地址操作之后，读取的是新数组的数据，都是有效数据。

**读操作**是没有加锁的，所以读是一直都能读：

```java
public E get(int index) {
    return get(getArray(), index);
}
```

---

## List<>里面填基本数据类型为什么会报错？ [重要性:B]

`List<>` 等泛型集合类要求填充的必须是引用类型（对象类型），而不能直接使用基本数据类型（如 int、char、double 等），否则会编译报错。

```java
// 错误示例：List 中直接使用基本数据类型 int
List<int> list = new ArrayList<>(); // 编译报错
```

解决的办法是，使用基本数据类型对应的包装类：

```java
// 正确示例：使用包装类 Integer
List<Integer> list = new ArrayList<>();
list.add(10); // 自动装箱：int -> Integer
int num = list.get(0); // 自动拆箱：Integer -> int
```

这么设计的原因是：
1. **泛型的类型擦除机制**：Java 泛型在编译后会被擦除为 Object 类型，而 Object 只能接收引用类型。
2. **历史原因**：Java 最初设计时基本数据类型和引用类型是严格区分的，泛型是后期（JDK 1.5）才引入的特性。

---

## List和数组如何互相转换？ [重要性:B]

### List 转数组

**无参 toArray()**（返回 Object[]，不推荐）：

```java
List<String> strList = new ArrayList<>();
strList.add("a");
strList.add("b");
Object[] objArr = strList.toArray(); // 返回Object[]，强转可能报错
```

**带参 toArray(T[] a)**（推荐，指定类型）：

```java
List<String> strList = new ArrayList<>();
strList.add("a");
strList.add("b");

// 方式1：传入指定长度的数组
String[] strArr1 = strList.toArray(new String[strList.size()]);
// 方式2：传入空数组（JDK1.8+更高效）
String[] strArr2 = strList.toArray(new String[0]);

// 自定义对象List转数组
List<User> userList = new ArrayList<>();
userList.add(new User("张三", 20));
User[] userArr = userList.toArray(new User[0]);
```

### 数组转 List

**普通对象数组转 List**（常用）：

```java
String[] strArr = {"a", "b", "c"};
// 返回固定大小的List（属于Arrays内部类，不可add/remove）
List<String> strList1 = Arrays.asList(strArr);

// 若需要可变List，包装一层ArrayList
List<String> strList2 = new ArrayList<>(Arrays.asList(strArr));
strList2.add("d"); // 正常执行
```

**基本类型数组转 List**（避坑）：

```java
// 错误示例：int[]转List会变成List<int[]>，而非List<Integer>
int[] numArr = {1, 2, 3};
List<int[]> wrongList = Arrays.asList(numArr);

// 正确方式1：手动装箱（JDK8-）
List<Integer> numList1 = new ArrayList<>();
for (int num : numArr) {
    numList1.add(num);
}

// 正确方式2：Stream流（JDK8+）
List<Integer> numList2 = Arrays.stream(numArr).boxed().collect(Collectors.toList());
```

---

# Set

![Set 继承层次结构](zmedia/Java集合面试题_images/07_set_hierarchy.png)

## Java 集合中 List 和 Set区别是什么？ [重要性:A]

Java 里 List 和 Set 作为 Collection 的核心子接口，最核心的区别就是"是否允许元素重复"和"是否保证有序"。

- **List**：有序的集合（存储顺序和添加顺序一致），允许元素重复，甚至可以存多个 null 值。能通过下标（索引）直接访问元素。适合需要按顺序存取、频繁根据位置访问元素的场景。
- **Set**：元素唯一，不允许重复。HashSet/LinkedHashSet 最多只能存一个 null 值（TreeSet 默认不允许 null）。默认不保证元素的存储顺序（除了 TreeSet、LinkedHashSet 等特殊实现）。没有下标，只能遍历。适合需要去重的场景。

补充特殊实现的差异：
- List 里的 Vector 是线程安全的，但性能差，现在基本不用。
- Set 里的 LinkedHashSet 既保证元素唯一，又能保留添加顺序。
- TreeSet 会按元素大小排序。
- ArrayList、HashSet 都是非线程安全的。

---

## 如何对Set排序？ [重要性:B]

Java 里 Set 本身默认不保证有序，核心是选带排序特性的 Set 实现类，或把普通 Set 转成有序结构。

### TreeSet（按值自动排序）

底层是红黑树，插入时自动排序，支持"自然排序"（元素实现 Comparable）和"自定义 Comparator 排序"。

```java
import java.util.TreeSet;
import java.util.Comparator;

public class SetSortDemo {
    // 1. 基本类型/字符串（自然排序）
    public static void testTreeSetBasic() {
        TreeSet<Integer> numSet = new TreeSet<>();
        numSet.add(3);
        numSet.add(1);
        numSet.add(2);
        // 遍历输出：1 2 3（自动按自然顺序升序）
        for (Integer num : numSet) {
            System.out.print(num + " ");
        }
    }

    // 2. 自定义对象（实现Comparable接口）
    static class User implements Comparable<User> {
        private String name;
        private int age;

        public User(String name, int age) {
            this.name = name;
            this.age = age;
        }

        // 重写compareTo，按年龄升序排序
        @Override
        public int compareTo(User o) {
            return this.age - o.age;
        }

        @Override
        public String toString() {
            return name + ":" + age;
        }
    }

    // 3. 自定义对象（传入Comparator，按年龄降序）
    public static void testTreeSetCustom() {
        TreeSet<User> userSet = new TreeSet<>(new Comparator<User>() {
            @Override
            public int compare(User u1, User u2) {
                return u2.age - u1.age; // 降序
            }
        });
        userSet.add(new User("张三", 20));
        userSet.add(new User("李四", 25));
        userSet.add(new User("王五", 22));
        // 遍历输出：李四:25 王五:22 张三:20（按年龄降序）
        for (User user : userSet) {
            System.out.println(user);
        }
    }

    // 4. LinkedHashSet：保留添加顺序（不按值排序）
    public static void testLinkedHashSet() {
        LinkedHashSet<String> strSet = new LinkedHashSet<>();
        strSet.add("b");
        strSet.add("a");
        strSet.add("c");
        // 遍历输出：b a c（和添加顺序一致）
        for (String str : strSet) {
            System.out.print(str + " ");
        }
    }
}
```

### LinkedHashSet（按插入顺序）

如果只是想按"插入顺序"遍历，不用按元素值排序，用 LinkedHashSet 即可，性能比 TreeSet 高：

```java
import java.util.LinkedHashSet;

public class LinkedHashSetDemo {
    public static void main(String[] args) {
        LinkedHashSet<String> strSet = new LinkedHashSet<>();
        strSet.add("b");
        strSet.add("a");
        strSet.add("c");
        // 遍历输出：b a c（严格按添加顺序）
        for (String str : strSet) {
            System.out.print(str + " ");
        }
    }
}
```

---

# Map

常见的 Map 集合（非线程安全）：

- **HashMap**：基于哈希表实现的 Map，根据键的哈希值来存储和获取键值对，JDK 1.8 中使用数组 + 链表 + 红黑树来实现。JDK 1.7 使用头插法 + 并发扩容时可能形成环形链表；JDK 1.8 改为尾插法后已经不会再出现死循环，但多线程 put() 仍存在数据覆盖和丢失等线程安全问题。
- **LinkedHashMap**：继承自 HashMap，在 HashMap 的基础上，使用双向链表维护了键值对的插入顺序或访问顺序。
- **TreeMap**：基于红黑树实现的 Map，可以对键进行排序，默认按照自然顺序排序，也可以通过指定的比较器进行排序。

常见的 Map 集合（线程安全）：

- **Hashtable**：早期 Java 提供的线程安全的 Map 实现，在方法上使用了 synchronized 关键字来保证线程安全。
- **ConcurrentHashMap**：JDK 1.8 以前采用了分段锁技术；JDK 1.8 以后通过 volatile + CAS 或者 synchronized 来保证线程安全。

---

## 如何对map进行快速遍历？ [重要性:B]

**1. 使用 for-each 循环和 entrySet() 方法**（最常见，可以同时获取键和值）：

```java
Map<String, Integer> map = new HashMap<>();
map.put("key1", 1);
map.put("key2", 2);
map.put("key3", 3);

for (Map.Entry<String, Integer> entry : map.entrySet()) {
    System.out.println("Key: " + entry.getKey() + ", Value: " + entry.getValue());
}
```

**2. 使用 for-each 循环和 keySet() 方法**（如果只需要遍历键）：

```java
for (String key : map.keySet()) {
    System.out.println("Key: " + key + ", Value: " + map.get(key));
}
```

**3. 使用迭代器**（在需要删除元素时比较有用）：

```java
Iterator<Entry<String, Integer>> iterator = map.entrySet().iterator();
while (iterator.hasNext()) {
    Entry<String, Integer> entry = iterator.next();
    System.out.println("Key: " + entry.getKey() + ", Value: " + entry.getValue());
}
```

**4. 使用 Lambda 表达式和 forEach() 方法**（Java 8+，最简洁）：

```java
map.forEach((key, value) -> System.out.println("Key: " + key + ", Value: " + value));
```

**5. 使用 Stream API**（Java 8+，可进行过滤、映射等操作）：

```java
map.entrySet().stream()
  .forEach(entry -> System.out.println("Key: " + entry.getKey() + ", Value: " + entry.getValue()));

// 还可以进行其他操作，如过滤、映射等
Map<String, Integer> filteredMap = map.entrySet().stream()
                                    .filter(entry -> entry.getValue() > 1)
                                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
```

---

## HashMap实现原理介绍一下？ [重要性:S]

在 JDK 1.7 版本之前，HashMap 数据结构是数组和链表。HashMap 通过哈希算法将元素的键（Key）映射到数组中的槽位（Bucket）。如果多个键映射到同一个槽位，它们会以链表的形式存储在同一个槽位上，因为链表的查询时间是 O(n)，所以冲突很严重时效率就很低了。

在 JDK 1.8 版本的时候做了优化：当某个桶的链表长度 ≥ 8（TREEIFY_THRESHOLD）且哈希表数组长度 ≥ 64（MIN_TREEIFY_CAPACITY）时，会把链表转换为红黑树，把该桶的查找时间复杂度从 O(n) 降低到 O(log n)；如果数组长度 < 64，则只会触发扩容（resize()），并不会立刻树化。反向地，在 resize() 过程中，若某个桶的节点数 ≤ 6（UNTREEIFY_THRESHOLD），红黑树会被退化回链表。

![HashMap JDK 1.7 结构（数组+链表）](zmedia/Java集合面试题_images/08_hashmap_before_8.webp)
*JDK 1.7 HashMap：数组 + 链表*

![HashMap JDK 1.8 结构（数组+链表+红黑树）](zmedia/Java集合面试题_images/09_hashmap_after_8.webp)
*JDK 1.8 HashMap：数组 + 链表 + 红黑树*

---

## HashMap链表发生转换后为什么不用平衡二叉树？ [重要性:A]

AVL 树是严格平衡的二叉树，要求任意节点的左右子树高度差不超过 1，这意味着：

- 插入/删除时会触发大量旋转操作（左旋、右旋、双旋），哪怕微小的高度差都要修正；
- HashMap 的场景是"链表转树"仅发生在链表长度 ≥ 8（JDK1.8）时，本身是低频场景，为了这种低频场景付出高频的平衡开销，完全不划算；
- 红黑树仅保证黑色高度平衡（不是严格的节点高度平衡），旋转次数远少于 AVL 树，插入/删除的平均时间复杂度仍为 O(log n)，但实际执行效率更高。

HashMap 的核心是"哈希 + 数组 + 链表/树"，树的作用只是解决哈希冲突严重导致链表过长的问题：

- 红黑树的查找、插入、删除的时间复杂度都是 O(log n)，虽然比 AVL 树的查找略慢（因为高度可能稍高），但增删的开销远低于 AVL 树；
- 对于 HashMap 来说，"增删"和"查找"的频率几乎持平，红黑树的综合性能更优。

---

## 了解的哈希冲突解决方法有哪些？ [重要性:A]

1. **链接法**：使用链表或其他数据结构来存储冲突的键值对，将它们链接在同一个哈希桶中。
2. **开放寻址法**：在哈希表中找到另一个可用的位置来存储冲突的键值对。常见的开放寻址方法包括线性探测、二次探测和双重散列。
3. **再哈希法（Rehashing）**：当发生冲突时，使用另一个哈希函数再次计算键的哈希值，直到找到一个空槽来存储键值对。
4. **哈希桶扩容**：当哈希冲突过多时，可以动态地扩大哈希桶的数量，重新分配键值对，以减少冲突的概率。

---

## HashMap是线程安全的吗？ [重要性:S]

HashMap 不是线程安全的，多线程会存在下面的问题：

- **JDK 1.7**：采用数组 + 链表的数据结构，多线程背景下，在数组扩容的时候，存在 Entry 链死循环和数据丢失问题。
- **JDK 1.8**：采用数组 + 链表 + 红黑二叉树的数据结构，优化了 1.7 中数组扩容的方案，解决了 Entry 链死循环和数据丢失问题。但是多线程背景下，put 方法存在数据覆盖的问题。

要保证线程安全，可以使用：
- `Collections.synchronizedMap()` 同步加锁的方式
- `Hashtable`（性能不达标）
- `ConcurrentHashMap`（更适合高并发场景）

ConcurrentHashMap 在 JDK 1.7 和 1.8 的版本改动比较大：
- **1.7** 使用 Segment + HashEntry 分段锁的方式实现
- **1.8** 抛弃了 Segment，改为使用 CAS + synchronized + Node 实现，同样也加入了红黑树

---

## 在 Java 的 hashmap 中 get一个元素的过程是怎样的？ [重要性:S]

`get` 方法的作用是传入我们需要获取的节点的 key，然后将这个节点的 value 返回。

```java
public V get(Object key) {
    Node<K,V> e;
    return (e = getNode(hash(key), key)) == null ? null : e.value;
}
```

`getNode` 方法的源码解读：

```java
final HashMap.Node<K,V> getNode(int hash, Object key) {
    HashMap.Node<K,V>[] tab; HashMap.Node<K,V> first, e; int n; K k;

    // 判断条件：table不为null、长度大于0、hash值计算出的位置有节点存在
    if ((tab = table) != null && (n = tab.length) > 0 &&
        (first = tab[(n - 1) & hash]) != null) {

        // 先判断第一个节点的key是否匹配
        if (first.hash == hash &&
            ((k = first.key) == key || (key != null && key.equals(k))))
            return first;

        // 遍历后续节点
        if ((e = first.next) != null) {
            // 如果是树节点，用红黑树查找算法
            if (first instanceof HashMap.TreeNode)
                return ((HashMap.TreeNode<K,V>)first).getTreeNode(hash, key);
            // 否则遍历链表
            do {
                if (e.hash == hash &&
                    ((k = e.key) == key || (key != null && key.equals(k))))
                    return e;
            } while ((e = e.next) != null);
        }
    }
    return null;
}
```

---

## hashmap的put过程介绍一下 [重要性:S]

HashMap 的 `put()` 方法用于向 HashMap 中添加键值对（JDK 1.8 版本）：

**第一步**：根据要添加的键的哈希码计算在数组中的位置（索引）。

**第二步**：检查该位置是否为空。
- 如果为空，则直接在该位置创建一个新的 Node 对象来存储键值对。

**第三步**：如果该位置已经存在其他键值对，检查该位置的第一个键值对的哈希码和键是否与要添加的键值对相同。
- 如果相同，直接替换值，完成更新操作。

**第四步**：如果第一个键值对不匹配，则需要遍历链表或红黑树来查找：
- 如果是链表结构，逐个比较直到找到相同的键或达到链表末尾。
  - 找到了相同的键，则更新值。
  - 没有找到，则将新的键值对添加到链表的尾部。
- 如果是红黑树结构，使用红黑树中的查找算法。
  - 找到了相同的键，则更新值。
  - 没有找到，则将新的键值对添加到红黑树中。

**第五步**：检查链表长度是否达到阈值（默认为8）。如果超过阈值且数组长度 ≥ 64，则将链表转换为红黑树。

**第六步**：检查负载因子是否超过阈值（默认为 0.75）。如果键值对的数量与数组的长度的比值大于阈值，则需要进行扩容操作。

**第七步**：扩容操作。创建一个新的两倍大小的数组，将旧数组中的每个键值对重新分配到新数组（要么原位置，要么原位置 + oldCap），无需重新计算 hash。

**第八步**：完成添加操作。

![HashMap put 流程](zmedia/Java集合面试题_images/10_hashmap_put_flow.png)
*HashMap put 操作完整流程*

---

## HashMap的put(key,val)和get(key)过程 [重要性:S]

存储对象时，将 K/V 传给 put 方法时，它调用 hashCode 计算 hash 从而得到 bucket 位置，进一步存储。HashMap 在每次 put 后会检查整个表的元素数量（size），当 size > 容量 × loadFactor（默认 16 × 0.75 = 12）时触发扩容，新容量为原来的 2 倍。

获取对象时，将 K 传给 get，它调用 hashCode 计算 hash 从而得到 bucket 位置，并进一步调用 equals() 方法确定键值对。如果发生碰撞的时候，Hashmap 通过链表将产生碰撞冲突的元素组织起来，在 Java 8 中，如果一个 bucket 中碰撞冲突的元素超过某个限制（默认是 8），则使用红黑树来替换链表，从而提高速度。

---

## hashmap 调用get方法一定安全吗？ [重要性:A]

不是，调用 get 方法有几点需要注意的地方：

1. **空指针异常（NullPointerException）**：
   - 如果 HashMap 变量本身是 null（还没 new），那么调用它的任何方法都会抛 NPE。
   - 如果 HashMap 已经正常初始化，那么用 null 作为 key 调用 `get(null)` / `put(null, v)` 都是合法的，不会抛 NPE，因为 HashMap 明确支持 null 键。

2. **线程安全**：HashMap 本身不是线程安全的。如果在多线程环境中，没有适当的同步措施，同时对 HashMap 进行读写操作可能会导致不可预测的行为。

---

## HashMap一般用什么做Key？为啥String适合做Key呢？ [重要性:A]

用 String 做 key，因为 String 对象是不可变的，一旦创建就不能被修改，这确保了 Key 的稳定性。如果 Key 是可变的，可能会导致 hashCode 和 equals 方法的不一致，进而影响 HashMap 的正确性。

---

## 为什么HashMap要用红黑树而不是平衡二叉树？ [重要性:A]

平衡二叉树追求的是一种"完全平衡"状态：任何结点的左右子树的高度差不会超过 1。这个要求太严了，导致每次进行插入/删除节点的时候，几乎都会破坏平衡规则，需要频繁通过左旋和右旋来进行调整。

红黑树不追求这种完全平衡状态，而是追求一种"弱平衡"状态：整个树最长路径不会超过最短路径的 2 倍。优势是虽然牺牲了一部分查找的性能效率，但是能够换取一部分维持树平衡状态的成本。与平衡树不同的是，红黑树在插入、删除等操作，不会像平衡树那样，频繁破坏红黑树的规则，所以不需要频繁调整。

---

## hashmap key可以为null吗？ [重要性:A]

可以为 null。

- HashMap 中使用 `hash()` 方法来计算 key 的哈希值，当 key 为空时，直接令 key 的哈希值为 0，不走 `key.hashCode()` 方法。
- HashMap 虽然支持 key 和 value 为 null，但是 null 作为 key 只能有一个，null 作为 value 可以有多个。
- 因为 HashMap 中，如果 key 值一样，那么会覆盖相同 key 值的 value 为最新，所以 key 为 null 只能有一个。

---

## 重写HashMap的equal和hashcode方法需要注意什么？ [重要性:S]

HashMap 使用 Key 对象的 `hashCode()` 和 `equals` 方法去决定 key-value 对的索引。如果这些方法没有被正确地实现，两个不同 Key 也许会产生相同的 `hashCode()` 和 `equals()` 输出，HashMap 将会认为它们是相同的，然后覆盖它们。

`equals()` 和 `hashCode()` 的实现应该遵循以下规则：

- 如果 `o1.equals(o2)`，那么 `o1.hashCode() == o2.hashCode()` 总是为 true 的。
- 如果 `o1.hashCode() == o2.hashCode()`，并不意味着 `o1.equals(o2)` 会为 true。

---

## 重写HashMap的equal方法不当会出现什么问题？ [重要性:A]

HashMap 在比较元素时，会先通过 hashCode 进行比较，相同的情况下再通过 equals 进行比较。

所以 equals 相等的两个对象，hashCode 一定相等。hashCode 相等的两个对象，equals 不一定相等（比如散列冲突的情况）。

重写了 equals 方法，不重写 hashCode 方法时，可能会出现 equals 方法返回为 true，而 hashCode 方法却返回 false，这样的后果会导致在 HashMap 等类中存储多个一模一样的对象，导致出现覆盖存储的数据的问题。

---

## 列举HashMap在多线程下可能会出现的问题？ [重要性:S]

1. **JDK 1.7 中的环形链表问题**：使用头插法插入元素，在多线程的环境下，扩容的时候有可能导致环形链表的出现，形成死循环。JDK 1.8 使用尾插法插入元素，在扩容时会保持链表元素原本的顺序，不会出现环形链表的问题。

2. **数据覆盖**：多线程同时执行 put 操作，如果计算出来的索引位置是相同的，那会造成前一个 key 被后一个 key 覆盖，从而导致元素的丢失。此问题在 JDK 1.7 和 JDK 1.8 中都存在。

---

## HashMap的扩容机制介绍一下 [重要性:S]

HashMap 默认的负载因子是 0.75，即如果 HashMap 中的元素个数超过了总容量 75%，则会触发扩容。扩容分为两个步骤：

1. 对哈希表长度的扩展（2 倍）
2. 将旧哈希表中的数据放到新的哈希表中

因为我们使用的是 2 次幂的扩展（指长度扩为原来 2 倍），所以元素的位置要么是在原位置，要么是在原位置再移动 2 次幂的位置。

因此在扩充 HashMap 时，不需要重新计算 hash，只需要看看原来的 hash 值新增的那个 bit 是 1 还是 0：
- 是 0 的话索引没变
- 是 1 的话索引变成"原索引 + oldCap"

这个设计既省去了重新计算 hash 值的时间，而且由于新增的 1bit 是 0 还是 1 可以认为是随机的，因此 resize 的过程均匀地把之前冲突的节点分散到新的 bucket 了。

![HashMap 扩容示意图](zmedia/Java集合面试题_images/11_hashmap_resize.png)
*HashMap 扩容（resize）流程*

---

## HashMap的大小为什么是2的n次方大小呢？ [重要性:S]

HashMap 底层是"数组 + 链表/红黑树"的结构，存的 key-value 时，第一步就是确定这个 key 存在数组的哪个位置（索引）。

HashMap 用的索引计算公式是：**索引 = hash & (length - 1)**

这个公式的设计初衷是用位运算替代取模运算，但它能生效的前提，就是 **length 必须是 2 的 n 次方**。

### 原因 1：保证"位运算等价于取模"，实现高效寻址

当 length 是 2 的 n 次方时，length - 1 的二进制低 n 位全是 1，高位全是 0。此时做"与运算"，相当于直接把 hash 值的低 n 位截取下来，在数学上等价于"对 length 取模"。

反例：如果 length = 15（不是 2 的 n 次方），length - 1 = 14，二进制是 00001110（最后一位是 0）。不管 hash 值的最后一位是 0 还是 1，与运算后都会变成 0——这就导致索引的最后一位永远用不到，比如索引 1、3、5、7... 这些位置永远不会存数据，既浪费了数组空间，又大大增加了哈希碰撞的概率。

### 原因 2：让哈希值的低位更均匀，减少碰撞

只有当 length - 1 的二进制是全 1 时，才能"接住"hash 值的均匀分布。比如 length=16 时，length-1=15（1111），hash 值的低 4 位每一位都能影响最终索引；如果 length=15，length-1=14（1110），最后一位直接失效，相当于少了一位来分散 hash，碰撞概率自然就高了。

### 原因 3：优化扩容时的元素重分配，不用重新算 hash

如果容量始终是 2 的 n 次方，扩容时元素的新索引就不用重新计算完整的 hash，只需要看 hash 值的某一个高位就行：

- 计算 `hash & oldCap`：如果结果为 0，新索引 = 旧索引；如果结果不为 0，新索引 = 旧索引 + oldCap。

整个过程只需要做一次"与运算"，速度非常快。而且还能把原来挤在同一个旧索引里的元素，均匀拆分到新数组的两个索引位。

![索引位运算示例](zmedia/Java集合面试题_images/12_hash_index_calc.webp)
*hash & (length - 1) 位运算示例*

![扩容 rehash 原理](zmedia/Java集合面试题_images/13_resize_rehash.webp)
*扩容时元素重新分布：无需重新计算 hash*

![扩容元素分布](zmedia/Java集合面试题_images/14_resize_redistribute.webp)
*16 扩容到 32 时元素的均匀拆分*

### 总结

HashMap 的大小设计为 2 的 n 次方，是一个环环相扣的优化设计：
1. 保证 `hash & (length - 1)` 等价于取模，用位运算实现高效寻址
2. 让 `length - 1` 的二进制全 1，接住 hash 值的均匀分布，减少碰撞
3. 为扩容优化铺路，不用重新算 hash，仅通过高位判断就能快速确定新索引

---

## 往hashmap存20个元素，会扩容几次？ [重要性:A]

当插入 20 个元素时，HashMap 的扩容过程如下：

- **初始容量**：16
  - 插入第 1 到第 12 个元素时，不需要扩容。
  - 插入第 13 个元素时，达到负载因子限制，需要扩容（16 → 32）。
- **扩容后的容量**：32
  - 插入第 14 到第 24 个元素时，不需要扩容。

因此，总共会进行一次扩容。

---

## 说说hashmap的负载因子 [重要性:S]

HashMap 负载因子 `loadFactor` 的默认值是 0.75，当 HashMap 中的元素个数超过了容量的 75% 时，就会进行扩容。

默认负载因子为 0.75，是因为它提供了空间和时间复杂度之间的良好平衡。负载因子太低会导致大量的空桶浪费空间，负载因子太高会导致大量的碰撞，降低性能。0.75 在这两个因素之间取得了良好的平衡。

---

## Hashmap和Hashtable有什么不一样的？Hashmap一般怎么用？ [重要性:A]

| 特性 | HashMap | Hashtable |
|------|---------|-----------|
| 线程安全 | 不安全 | 安全（synchronized） |
| 效率 | 高 | 低 |
| null key/value | 支持 null key（只能一个）和 null value（多个） | 不支持 null key 和 value |
| 默认初始容量 | 16 | 11 |
| 扩容 | 变为原来 2 倍 | 变为原来的 2n+1 |
| 底层结构 | 数组+链表/红黑树 | 数组+链表 |

HashMap 主要用来存储键值对，调用 `put` 方法向其中加入元素，调用 `get` 方法获取某个键对应的值，通过 `containsKey` 方法查看某个键是否存在等。

![HashMap vs Hashtable 对比](zmedia/Java集合面试题_images/17_hashmap_vs_hashtable.png)
*HashMap 和 Hashtable 的对比*

---

## ConcurrentHashMap怎么实现的？ [重要性:S]

### JDK 1.7 ConcurrentHashMap

使用数组加链表的形式实现，数组分为大数组 Segment 和小数组 HashEntry。Segment 是一种可重入锁（ReentrantLock），在 ConcurrentHashMap 里扮演锁的角色。分段锁技术将数据分成一段一段的存储，然后给每一段数据配一把锁，当一个线程占用锁访问其中一个段数据的时候，其他段的数据也能被其他线程访问。

![ConcurrentHashMap JDK 1.7 结构（分段锁）](zmedia/Java集合面试题_images/15_concurrenthashmap_17.webp)
*JDK 1.7 ConcurrentHashMap：Segment + HashEntry 分段锁*

### JDK 1.8 ConcurrentHashMap

主要使用 volatile + CAS 或者 synchronized 来实现线程安全：

- 添加元素时首先会判断容器是否为空：
  - 如果为空则使用 volatile 加 CAS 来初始化
  - 如果根据存储的元素计算结果为空，则利用 CAS 设置该节点
  - 如果根据存储的元素计算结果不为空，则使用 synchronized，然后遍历桶中的数据，并替换或新增节点到桶中
  - 最后再判断是否需要转为红黑树

JDK 1.8 通过对头结点加锁来保证线程安全，锁的粒度相比 Segment 更小了，并发操作的性能提高了。而且使用红黑树优化了之前的固定链表，查询性能从 O(n) 优化到了 O(log n)。

![ConcurrentHashMap JDK 1.8 结构（CAS + synchronized）](zmedia/Java集合面试题_images/16_concurrenthashmap_18.webp)
*JDK 1.8 ConcurrentHashMap：CAS + volatile + synchronized*

---

## JDK 1.7 中的分段锁是怎么加锁的？ [重要性:A]

注意：分段锁是 JDK 1.7 ConcurrentHashMap 的实现，JDK 1.8 之后已经废弃了 Segment，改为对桶头节点加 synchronized。

在 JDK 1.7 的 ConcurrentHashMap 中，将整个数据结构分为多个 Segment，每个 Segment 都类似于一个小的 HashMap，每个 Segment 都有自己的锁，不同 Segment 之间的操作互不影响。

对于插入、更新、删除等操作，需要先定位到具体的 Segment，然后再在该 Segment 上加锁，而不是像 Hashtable 那样对整个表加锁。

---

## 分段锁是可重入的吗？ [重要性:B]

JDK 1.7 ConcurrentHashMap 中的分段锁使用了 ReentrantLock，是一个可重入的锁。

---

## 已经用了synchronized，为什么还要用CAS呢？ [重要性:A]

ConcurrentHashMap 使用这两种手段来保证线程安全是一种权衡的考虑，根据锁竞争程度来判断：

- 在 `putVal` 中，如果计算出来的 hash 槽没有存放元素，可以直接使用 CAS 来进行设置值。因为 hash 值经过了各种扰动后，造成 hash 碰撞的几率较低，可以使用较少的自旋来完成具体的 hash 落槽操作。
- 当桶位已经存在节点（发生 hash 碰撞）时，需要遍历链表或红黑树进行查找、替换或追加节点，操作步骤较多且需要保护整条链/树的结构，CAS 自旋已经不再适合，因此改用 synchronized 锁住桶的头节点来完成这部分逻辑。

---

## ConcurrentHashMap用了悲观锁还是乐观锁? [重要性:A]

悲观锁和乐观锁都有用到。

- 如果容器为空，或计算结果为空：使用 volatile 加 **CAS（乐观锁）** 来初始化/设置节点。
- 如果计算结果不为空：使用 **synchronized（悲观锁）**，遍历桶中的数据，替换或新增节点到桶中，最后判断是否需要转为红黑树。

---

## Hashtable 底层实现原理是什么？ [重要性:B]

Hashtable 的底层数据结构主要是数组加上链表，数组是主体，链表是解决 hash 冲突存在的。

Hashtable 是线程安全的，实现方式是 Hashtable 的所有公共方法均采用 synchronized 关键字，当一个线程访问同步方法，另一个线程也访问的时候，就会陷入阻塞或者轮询的状态。

---

## Hashtable线程安全是怎么实现的？ [重要性:B]

因为它的 put、get 做成了同步方法，保证了 Hashtable 的线程安全性。每个操作数据的方法都进行同步控制之后，由此带来的问题是任何一个时刻只能有一个线程可以操纵 Hashtable，所以效率比较低。

Hashtable 的 `put(K key, V value)` 和 `get(Object key)` 方法的源码：

```java
public synchronized V put(K key, V value) {
    // Make sure the value is not null
    if (value == null) {
        throw new NullPointerException();
    }
    // Makes sure the key is not already in the hashtable.
    Entry<?,?> tab[] = table;
    int hash = key.hashCode();
    int index = (hash & 0x7FFFFFFF) % tab.length;
    @SuppressWarnings("unchecked")
    Entry<K,V> entry = (Entry<K,V>)tab[index];
    for(; entry != null ; entry = entry.next) {
        if ((entry.hash == hash) && entry.key.equals(key)) {
            V old = entry.value;
            entry.value = value;
            return old;
        }
    }
    addEntry(hash, key, value, index);
    return null;
}

public synchronized V get(Object key) {
    Entry<?,?> tab[] = table;
    int hash = key.hashCode();
    int index = (hash & 0x7FFFFFFF) % tab.length;
    for (Entry<?,?> e = tab[index] ; e != null ; e = e.next) {
        if ((e.hash == hash) && e.key.equals(key)) {
            return (V)e.value;
        }
    }
    return null;
}
```

---

## hashtable 和concurrentHashMap有什么区别 [重要性:A]

| 比较维度 | ConcurrentHashMap | Hashtable |
|---------|------------------|-----------|
| 底层数据结构（JDK 1.7） | 分段的数组 + 链表 | 数组 + 链表 |
| 底层数据结构（JDK 1.8） | 数组 + 链表/红黑树 | — |
| 线程安全实现（JDK 1.7） | 分段锁（Segment 锁） | synchronized 锁整个表 |
| 线程安全实现（JDK 1.8） | CAS + synchronized | — |
| 锁粒度 | 段级（1.7）或桶级（1.8） | 整个表 |
| 并发性能 | 高 | 低 |

---

## 说一下HashMap和Hashtable、ConcurrentMap的区别 [重要性:A]

**HashMap**：线程不安全，效率高，可以存储 null 的 key 和 value。默认初始容量为 16，每次扩充变为原来 2 倍。底层数据结构为数组+链表，插入元素后如果链表长度大于阈值（默认为8），先判断数组长度是否小于64，如果小于则扩充数组，反之将链表转化为红黑树。

**Hashtable**：线程安全（synchronized），效率低，不可以有 null 的 key 和 value。默认初始容量为 11，每次扩容变为原来的 2n+1。底层数据结构为数组+链表。基本被淘汰了。

**ConcurrentHashMap**：线程安全，不支持 null key 或 null value（会抛 NPE），原因是多线程下 null 无法区分"key 不存在"还是"key 对应的 value 就是 null"。
- JDK 1.7 及以前：基于分段锁实现
- JDK 1.8 及以后：取消 Segment，基于 volatile + CAS + synchronized，锁粒度从"段"缩小到"桶"

---

# Set

## Set集合有什么特点？如何实现key无重复的？ [重要性:A]

**特点**：Set 集合中的元素是唯一的，不会出现重复的元素。

**实现原理**：

- **HashSet / LinkedHashSet**：底层是哈希表，插入元素时先用 `hashCode()` 定位桶，再用 `equals()` 比较是否已存在相同元素，存在则不再插入。
- **TreeSet**：底层是红黑树，插入元素时不调用 hashCode/equals，而是用 `Comparable.compareTo()`（自然排序）或自定义 `Comparator.compare()` 的返回值是否为 0 来判断是否重复。

---

## 有序的Set是什么？记录插入顺序的集合是什么？ [重要性:B]

"有序"的 Set 有 TreeSet 和 LinkedHashSet，但两者"有序"的含义并不一样：

- **TreeSet** 基于红黑树实现，元素按"自然顺序（natural ordering，即 Comparable.compareTo() 定义的顺序）"或自定义 Comparator 排序存储，属于"按值排序"。
- **LinkedHashSet** 基于哈希表 + 双向链表实现，链表记录了元素的插入顺序，遍历时按插入顺序输出，属于"保留插入顺序"（和元素值的大小无关）。

记录插入顺序的集合通常指的是 **LinkedHashSet**，它既保证元素唯一，又能按插入顺序遍历，当需要"去重 + 保留添加顺序"时它是首选。

---

> 上次更新: 2026-05-16
